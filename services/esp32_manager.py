#!/usr/bin/env python3
"""
ESP32Manager - Versión Corregida y Simplificada
Basada en el test manual que SÍ funciona
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
        """Establecer conexión serial - SIMPLIFICADO"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔌 Intento de conexión {attempt + 1}/{max_retries}")
                
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                
                # Abrir puerto serial - exactamente como el test manual
                self.serial_conn = serial.Serial(
                    port=settings.SERIAL_PORT,
                    baudrate=settings.SERIAL_BAUDRATE,
                    timeout=5,  # Timeout más largo
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                # Esperar un poco para estabilizar conexión
                await asyncio.sleep(1)
                
                # Test simple - exactamente como tu comando manual
                success = await self._simple_test()
                
                if success:
                    self.connected = True
                    self.communication_errors = 0
                    logger.info(f"✅ Conectado al ESP32 en {settings.SERIAL_PORT}")
                    return True
                else:
                    logger.warning(f"⚠️ Test de conexión falló en intento {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"❌ Intento {attempt + 1} falló: {e}")
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                await asyncio.sleep(1)
        
        self.connected = False
        return False
    
    async def _simple_test(self) -> bool:
        """Test simple - replica exactamente tu comando manual"""
        try:
            logger.debug("🧪 Ejecutando test simple...")
            
            # Limpiar buffers
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            # Enviar comando - exactamente como tu test
            self.serial_conn.write(b"CMD:GET_DATA\n")
            self.serial_conn.flush()
            
            # Leer respuesta - exactamente como tu test
            response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            
            logger.debug(f"🔍 Respuesta del test: {response[:100]}...")
            
            # Verificar si es una respuesta válida
            if response and (response.startswith("DATA:") or response.startswith("HEARTBEAT:")):
                logger.debug("✅ Test simple exitoso")
                return True
            else:
                logger.debug("❌ Test simple falló - respuesta inválida")
                return False
                
        except Exception as e:
            logger.debug(f"❌ Test simple falló con excepción: {e}")
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
        """Enviar comando síncronamente - SIMPLIFICADO"""
        if not self.connected or not self.serial_conn:
            raise ESP32CommunicationError("ESP32 no conectado")
        
        try:
            logger.debug(f"📤 Enviando comando: {command}")
            
            # Limpiar buffer de entrada
            self.serial_conn.reset_input_buffer()
            
            # Enviar comando - exactamente como tu test manual
            cmd_bytes = f"{command}\n".encode('utf-8')
            self.serial_conn.write(cmd_bytes)
            self.serial_conn.flush()
            
            # Esperar un poco
            time.sleep(0.1)
            
            # Leer respuesta según el tipo de comando
            if command == "CMD:GET_DATA":
                response = self._read_data_response()
            else:
                response = self._read_simple_response()
            
            if response:
                self.last_successful_communication = time.time()
                self.communication_errors = 0
                logger.debug(f"📥 Respuesta recibida: {response[:100]}...")
                return response
            else:
                logger.warning("⚠️ No se recibió respuesta")
                return None
            
        except Exception as e:
            self.communication_errors += 1
            if self.communication_errors > 5:
                self.connected = False
                logger.error("🔴 Demasiados errores de comunicación, desconectando")
            raise ESP32CommunicationError(f"Error de comunicación: {e}")
    
    def _read_data_response(self) -> Optional[str]:
        """Leer respuesta DATA - exactamente como tu test manual"""
        try:
            # Usar readline exactamente como en tu test
            response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            
            if response and response.startswith("DATA:"):
                # Verificar que el JSON sea válido
                try:
                    json_str = response[5:]  # Remover "DATA:"
                    json.loads(json_str)  # Validar JSON
                    return response
                except json.JSONDecodeError:
                    logger.warning("⚠️ JSON inválido recibido")
                    return None
            else:
                logger.debug(f"⚠️ Respuesta no es DATA: {response[:50]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error leyendo respuesta DATA: {e}")
            return None
    
    def _read_simple_response(self) -> Optional[str]:
        """Leer respuesta simple (OK:, ERROR:, etc)"""
        try:
            response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            
            if response and (response.startswith("OK:") or response.startswith("ERROR:") or response.startswith("HEARTBEAT:")):
                return response
            else:
                logger.debug(f"⚠️ Respuesta simple inesperada: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error leyendo respuesta simple: {e}")
            return None
    
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
            logger.warning(f"⚠️ Respuesta inválida del ESP32: {response}")
            return None
        
        try:
            # Parsear JSON - exactamente como debería funcionar
            json_str = response[5:]  # Remover "DATA:"
            data_dict = json.loads(json_str)
            
            # Convertir a modelo Pydantic
            esp32_data = ESP32Data(**data_dict)
            self.last_data = data_dict
            
            logger.debug("✅ Datos parseados correctamente")
            return esp32_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            logger.error(f"JSON problemático: {response[:200]}...")
            return None
        except Exception as e:
            logger.error(f"❌ Error creando modelo: {e}")
            # Mostrar qué campos faltan
            if isinstance(e, TypeError) and "required positional argument" in str(e):
                logger.error(f"Campos en JSON: {list(data_dict.keys()) if 'data_dict' in locals() else 'No se pudo parsear'}")
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
            "queue_size": self.command_queue.qsize() if self.command_queue else 0
        }
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Información de debug"""
        return {
            "manager_running": self.running,
            "serial_open": self.serial_conn.is_open if self.serial_conn else False,
            "worker_alive": self.worker_thread.is_alive() if self.worker_thread else False,
            "last_data_keys": list(self.last_data.keys()) if self.last_data else [],
            "request_times_count": len(self.request_times)
        }