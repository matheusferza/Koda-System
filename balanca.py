import re
import threading
import time

import serial
from serial.tools import list_ports


class BalancaSerial:
    def __init__(self, porta, baud_rate=9600):
        self.porta = porta
        self.baud_rate = baud_rate
        self.conexao = None
        self._connected = False
        self.peso_atual = 0.0
        self._peso_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._reader_thread = None
        self._last_connect_attempt = 0.0
        self._connected = False
        self._last_read_at = 0.0
        self._last_error = "Aguardando comunicacao"

        self.conectar()
        self._start_reader_thread()

    def _candidate_ports(self):
        explicit = []
        if self.porta and str(self.porta).upper() != 'AUTO':
            explicit.append(self.porta)

        preferred = []
        generic = []
        for info in list_ports.comports():
            desc = (info.description or '').upper()
            device = info.device
            if device in explicit:
                continue
            if 'BEMATECH' in desc or 'MP-4200' in desc:
                continue
            if any(token in desc for token in ('CH340', 'USB-SERIAL', 'USB SERIAL', 'CP210', 'SILICON LABS', 'ARDUINO', 'FTDI')):
                preferred.append(device)
            else:
                generic.append(device)

        ordered = explicit + preferred + generic
        seen = set()
        result = []
        for port in ordered:
            if port not in seen:
                seen.add(port)
                result.append(port)
        return result

    def conectar(self):
        if self.conexao is not None and self.conexao.is_open:
            return True

        now = time.monotonic()
        if now - self._last_connect_attempt < 1.0:
            return False
        self._last_connect_attempt = now

        candidate_ports = self._candidate_ports()
        if not candidate_ports:
            self._last_error = 'Nenhuma porta serial disponivel'
            self._connected = False
            return False

        last_exc = None
        for port in candidate_ports:
            try:
                self.conexao = serial.Serial(
                    port=port,
                    baudrate=self.baud_rate,
                    timeout=0.05,
                    write_timeout=0.05,
                )
                self.conexao.reset_input_buffer()
                self.porta = port
                self._connected = True
                self._last_error = f'Conectada em {port}'
                return True
            except serial.SerialException as exc:
                self.conexao = None
                self._connected = False
                last_exc = exc

        self._last_error = str(last_exc) if last_exc else 'Falha ao abrir a porta serial'
        return False

    def _start_reader_thread(self):
        if self._reader_thread and self._reader_thread.is_alive():
            return

        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _reader_loop(self):
        while not self._stop_event.is_set():
            if not self.conectar():
                self._stop_event.wait(0.5)
                continue

            try:
                self.conexao.write(b'\x05')
                linha_bytes = self.conexao.readline()
                if linha_bytes:
                    self._processar_linha(linha_bytes.decode('utf-8', errors='ignore'))
                    self._connected = True
                    self._last_error = "Conectada"
                    self._last_read_at = time.monotonic()
            except (serial.SerialException, OSError) as exc:
                self._last_error = str(exc)
                self._connected = False
                self._fechar_conexao()
                self._stop_event.wait(0.4)
            except Exception as exc:
                self._last_error = str(exc)
                self._stop_event.wait(0.15)

            self._stop_event.wait(0.12)

    def _processar_linha(self, linha):
        if "PESO L:" not in linha:
            return

        match = re.search(r'PESO L:\s*([\d\.,]+)', linha)
        if not match:
            return

        try:
            peso = float(match.group(1).replace(',', '.'))
        except ValueError:
            return

        if peso < 0.002:
            peso = 0.0

        with self._peso_lock:
            self.peso_atual = peso

    def ler_peso_instantaneo(self):
        self._start_reader_thread()
        with self._peso_lock:
            return self.peso_atual

    def obter_status(self):
        self._start_reader_thread()
        with self._peso_lock:
            return {
                "connected": self._connected and self.conexao is not None and self.conexao.is_open,
                "weight": self.peso_atual,
                "last_read_age": None if not self._last_read_at else max(0.0, time.monotonic() - self._last_read_at),
                "last_error": self._last_error,
                "port": self.porta,
            }

    def _fechar_conexao(self):
        if self.conexao and self.conexao.is_open:
            try:
                self.conexao.close()
            except Exception:
                pass
        self.conexao = None

    def fechar(self):
        self._stop_event.set()
        self._fechar_conexao()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=0.3)
