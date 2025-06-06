#!/usr/bin/env python3
"""
Manager robusto para comunicación con ESP32
"""

import serial
import json
import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
import queue
from core.config import settings
from core.logger import logger
from models.esp32_data import ESP32Data

class ESP32CommunicationError(Exception):
    """Excepción para errores de comunicación"""
    pass

class ESP32Manager:
    """Manager principal para comunicación con ESP32"""
    
    def __init__(self):
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
        self.last_command_time = 0
        self.lock = threading.Lock()
        self.running = False
        
        # Cache y estado
        self.last_data: Optional[Dict[str, Any]] = None
        self.last_successful_communication = time.time()
        self.communication_errors = 0
        
        # Cola de comandos para rate limiting
        self.command_queue = queue.Queue(maxsize=10)
        self.worker_thread: Optional[threading.Thread] = None
        
        # Rate limiting
        self.request_times = []
        
    async def start(self) -> bool:
        """Inicializar manager y conectar"""
        logger.info("🚀 Iniciando ESP32 Manager...")
        
        if await self._connect():
            self.running = True
            self._start_worker_thread()
            logger.info("✅ ESP32 Manager iniciado correctamente")
            return True
        
        logger.error("❌ Error iniciando ESP32 Manager")
        return False
    
    async def stop(self):
        """Detener manager"""
        logger.info("🛑 Deteniendo ESP32 Manager...")
        self.running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        
        self.connected = False
        logger.info("✅ ESP32 Manager detenido")
    
    async def _connect(self) -> bool:
        """Establecer conexión serial"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                
                self.serial_conn = serial.Serial(
                    port=settings.SERIAL_PORT,
                    baudrate=settings.SERIAL_BAUDRATE,
                    timeout=settings.SERIAL_TIMEOUT,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                # Limpiar buffers
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # Probar comunicación
                if await self._test_communication():
                    self.connected = True
                    self.communication_errors = 0
                    logger.info(f"✅ Conectado al ESP32 en {settings.SERIAL_PORT}")
                    return True
                
            except Exception as e:
                logger.warning(f"❌ Intento {attempt + 1}: {e}")
                await asyncio.sleep(1)
        
        self.connected = False
        return False
    
    async def _test_communication(self) -> bool:
        """Probar comunicación básica"""
        try:
            response = await self._send_command_raw("CMD:GET_DATA", expect_response=False)
            return response is not None
        except Exception:
            return False
    
    def _start_worker_thread(self):
        """Iniciar hilo worker para procesar comandos"""
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Loop principal para procesar comandos en cola"""
        while self.running:
            try:
                # Procesar comando con timeout
                command_data = self.command_queue.get(timeout=1.0)
                command, callback, timeout = command_data
                
                # Rate limiting
                if not self._can_send_request():
                    callback(None, "Rate limit exceeded")
                    continue
                
                # Enviar comando
                try:
                    response = self._send_command_sync(command)
                    callback(response, None)
                except Exception as e:
                    callback(None, str(e))
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error en worker loop: {e}")
    
    def _can_send_request(self) -> bool:
        """Verificar rate limiting"""
        now = time.time()
        
        # Limpiar requests viejos
        self.request_times = [t for t in self.request_times if (now - t) < 60]
        
        # Verificar límite por minuto
        if len(self.request_times) >= settings.MAX_REQUESTS_PER_MINUTE:
            return False
        
        # Verificar intervalo mínimo
        if self.request_times and (now - self.request_times[-1]) < settings.MIN_COMMAND_INTERVAL:
            return False
        
        self.request_times.append(now)
        return True
    
    def _send_command_sync(self, command: str) -> Optional[str]:
        """Enviar comando síncronamente (para worker thread)"""
        if not self.connected or not self.serial_conn:
            raise ESP32CommunicationError("ESP32 no conectado")
        
        try:
            # Limpiar buffer
            self.serial_conn.reset_input_buffer()
            
            # Enviar comando
            cmd_bytes = f"{command}\n".encode('utf-8')
            self.serial_conn.write(cmd_bytes)
            self.serial_conn.flush()
            
            # Leer respuesta
            response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            
            if response:
                self.last_successful_communication = time.time()
                self.communication_errors = 0
                return response
            
            return None
            
        except Exception as e:
            self.communication_errors += 1
            if self.communication_errors > 5:
                self.connected = False
            raise ESP32CommunicationError(f"Error de comunicación: {e}")
    
    async def _send_command_raw(self, command: str, expect_response: bool = True) -> Optional[str]:
        """Enviar comando raw async"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._send_command_sync, command
        )
    
    async def get_data(self) -> Optional[ESP32Data]:
        """Obtener datos completos del ESP32"""
        def callback_wrapper(response, error):
            callback_wrapper.result = (response, error)
        
        # Agregar comando a la cola
        try:
            self.command_queue.put(("CMD:GET_DATA", callback_wrapper, 10), timeout=1)
        except queue.Full:
            logger.warning("⚠️ Cola de comandos llena")
            return None
        
        # Esperar respuesta
        start_time = time.time()
        while not hasattr(callback_wrapper, 'result') and (time.time() - start_time) < 10:
            await asyncio.sleep(0.1)
        
        if not hasattr(callback_wrapper, 'result'):
            logger.error("❌ Timeout esperando respuesta")
            return None
        
        response, error = callback_wrapper.result
        
        if error:
            logger.error(f"❌ Error obteniendo datos: {error}")
            return None
        
        if not response or not response.startswith("DATA:"):
            logger.warning("⚠️ Respuesta inválida del ESP32")
            return None
        
        try:
            # Parsear JSON
            json_str = response[5:]  # Remover "DATA:"
            data_dict = json.loads(json_str)
            
            # Convertir a modelo Pydantic
            esp32_data = ESP32Data(**data_dict)
            self.last_data = data_dict
            
            return esp32_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creando modelo: {e}")
            return None
    
    async def set_parameter(self, parameter: str, value: Any) -> bool:
        """Establecer un parámetro"""
        # Convertir valor a string apropiado
        if isinstance(value, bool):
            value_str = str(value).lower()
        else:
            value_str = str(value)
        
        command = f"CMD:SET_{parameter}:{value_str}"
        
        def callback_wrapper(response, error):
            callback_wrapper.result = (response, error)
        
        try:
            self.command_queue.put((command, callback_wrapper, 5), timeout=1)
        except queue.Full:
            logger.warning("⚠️ Cola de comandos llena")
            return False
        
        # Esperar respuesta
        start_time = time.time()
        while not hasattr(callback_wrapper, 'result') and (time.time() - start_time) < 5:
            await asyncio.sleep(0.1)
        
        if not hasattr(callback_wrapper, 'result'):
            return False
        
        response, error = callback_wrapper.result
        
        if error:
            logger.error(f"❌ Error configurando {parameter}: {error}")
            return False
        
        success = response and response.startswith("OK:")
        if success:
            logger.info(f"✅ {parameter} configurado a {value}")
        else:
            logger.error(f"❌ Error configurando {parameter}: {response}")
        
        return success
    
    async def toggle_load(self, total_seconds: int) -> bool:
        """Apagar carga temporalmente"""
        if total_seconds < 1 or total_seconds > 43200:
            logger.error("❌ Duración fuera de rango")
            return False
        
        command = f"CMD:TOGGLE_LOAD:{total_seconds}"
        
        def callback_wrapper(response, error):
            callback_wrapper.result = (response, error)
        
        try:
            self.command_queue.put((command, callback_wrapper, 5), timeout=1)
        except queue.Full:
            return False
        
        # Esperar respuesta
        start_time = time.time()
        while not hasattr(callback_wrapper, 'result') and (time.time() - start_time) < 5:
            await asyncio.sleep(0.1)
        
        if not hasattr(callback_wrapper, 'result'):
            return False
        
        response, error = callback_wrapper.result
        
        if error:
            logger.error(f"❌ Error en toggle_load: {error}")
            return False
        
        success = response and response.startswith("OK:")
        if success:
            logger.info(f"✅ Carga apagada por {total_seconds} segundos")
        
        return success
    
    async def cancel_temporary_off(self) -> bool:
        """Cancelar apagado temporal"""
        def callback_wrapper(response, error):
            callback_wrapper.result = (response, error)
        
        try:
            self.command_queue.put(("CMD:CANCEL_TEMP_OFF", callback_wrapper, 5), timeout=1)
        except queue.Full:
            return False
        
        # Esperar respuesta
        start_time = time.time()
        while not hasattr(callback_wrapper, 'result') and (time.time() - start_time) < 5:
            await asyncio.sleep(0.1)
        
        if not hasattr(callback_wrapper, 'result'):
            return False
        
        response, error = callback_wrapper.result
        
        if error:
            logger.error(f"❌ Error cancelando apagado: {error}")
            return False
        
        success = response and response.startswith("OK:")
        if success:
            logger.info("✅ Apagado temporal cancelado")
        
        return success
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtener información de conexión"""
        return {
            "connected": self.connected,
            "port": settings.SERIAL_PORT,
            "baudrate": settings.SERIAL_BAUDRATE,
            "last_communication": self.last_successful_communication,
            "communication_errors": self.communication_errors,
            "queue_size": self.command_queue.qsize()
        }