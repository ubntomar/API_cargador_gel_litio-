#!/usr/bin/env python3
"""
ESP32Manager - Comunicación Serial con Protección Anti-Congelamiento
"""

import serial
import json
import time
import asyncio
import threading
from typing import Optional, Dict, Any
from core.config import settings
from core.logger import logger
from models.esp32_data import ESP32Data

class ESP32Manager:
    def __init__(self):
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
        self.communication_errors = 0
        self.lock = threading.Lock()
        self.last_successful_communication = time.time()
        
        # ✅ NUEVO: Cache para prevenir requests excesivas
        self._last_data: Optional[ESP32Data] = None
        self._last_data_time: float = 0
        self._cache_duration: float = 1.0  # 1 segundo de cache mínimo
        
    async def start(self) -> bool:
        """Inicializar manager y conectar"""
        logger.info("🚀 Iniciando ESP32 Manager con protección anti-congelamiento...")
        
        if await self._connect():
            logger.info("✅ ESP32 Manager iniciado correctamente")
            return True
        
        logger.error("❌ Error iniciando ESP32 Manager")
        return False
    
    async def _connect(self) -> bool:
        """Establecer conexión serial con timeout"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔌 Intento {attempt + 1}: Conectando a {settings.SERIAL_PORT}")
                
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                
                self.serial_conn = serial.Serial(
                    port=settings.SERIAL_PORT,
                    baudrate=settings.SERIAL_BAUDRATE,
                    timeout=min(settings.SERIAL_TIMEOUT, 2.0),  # ✅ Máximo 2s timeout
                    write_timeout=1.0,  # ✅ NUEVO: Timeout de escritura
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                # Limpiar buffers
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # Probar comunicación con timeout corto
                if await self._test_communication():
                    self.connected = True
                    self.communication_errors = 0
                    logger.info(f"✅ Conectado al ESP32 en {settings.SERIAL_PORT}")
                    return True
                else:
                    logger.warning(f"❌ No se pudo comunicar con ESP32 en intento {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"❌ Intento {attempt + 1} falló: {e}")
                await asyncio.sleep(min(1, attempt))  # ✅ Backoff progresivo
        
        self.connected = False
        return False
    
    async def _test_communication(self) -> bool:
        """Probar comunicación con timeout agresivo"""
        try:
            logger.info("🧪 Probando comunicación con ESP32...")
            
            # ✅ NUEVO: Test rápido con timeout muy corto
            response = await self._send_command("CMD:GET_DATA", timeout=2.0)
            
            if response and (response.startswith("DATA:") or "panelToBatteryCurrent" in response):
                logger.info("✅ Comunicación con ESP32 exitosa")
                return True
            else:
                logger.warning(f"⚠️ Respuesta inesperada del ESP32: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando comunicación: {e}")
            return False
    
    async def _send_command(self, command: str, timeout: float = 3.0) -> Optional[str]:
        """Enviar comando con protección anti-congelamiento"""
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("❌ Puerto serial no está abierto")
            return None
        
        # ✅ NUEVO: Timeout máximo absoluto
        max_timeout = min(timeout, 5.0)
        
        try:
            # ✅ CORREGIDO: Lock con timeout
            if not self.lock.acquire(timeout=2.0):
                logger.error("❌ Timeout obteniendo lock para comunicación serial")
                return None
            
            try:
                logger.debug(f"📤 Enviando: {command}")
                
                # Limpiar buffer de entrada
                self.serial_conn.reset_input_buffer()
                
                # ✅ NUEVO: Enviar comando con manejo de excepciones
                try:
                    command_bytes = (command + '\n').encode('utf-8')
                    self.serial_conn.write(command_bytes)
                    self.serial_conn.flush()
                except serial.SerialTimeoutException:
                    logger.error("❌ Timeout escribiendo comando serial")
                    return None
                
                # ✅ CORREGIDO: Lectura con timeout más agresivo
                start_time = time.time()
                response = ""
                no_data_count = 0
                max_no_data = 50  # Máximo 50 iteraciones sin datos
                
                while (time.time() - start_time) < max_timeout:
                    try:
                        if self.serial_conn.in_waiting > 0:
                            no_data_count = 0
                            chunk = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8')
                            response += chunk
                            
                            # Buscar línea completa
                            if '\n' in response:
                                lines = response.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line and (line.startswith('DATA:') or 
                                               line.startswith('OK:') or 
                                               line.startswith('ERROR:') or
                                               'panelToBatteryCurrent' in line):
                                        logger.debug(f"📥 Recibido: {line[:100]}...")
                                        self.last_successful_communication = time.time()
                                        return line
                        else:
                            no_data_count += 1
                            if no_data_count >= max_no_data:
                                logger.warning("❌ Demasiadas iteraciones sin datos")
                                break
                        
                        # ✅ CORREGIDO: Sleep más largo para reducir CPU usage
                        await asyncio.sleep(0.05)  # 50ms en lugar de 10ms
                        
                    except UnicodeDecodeError:
                        logger.warning("⚠️ Error decodificando respuesta")
                        await asyncio.sleep(0.1)
                        continue
                    except Exception as e:
                        logger.error(f"❌ Error leyendo serial: {e}")
                        break
                
                logger.warning(f"⏰ Timeout esperando respuesta para: {command}")
                return None
                
            finally:
                self.lock.release()
                
        except Exception as e:
            logger.error(f"❌ Error enviando comando '{command}': {e}")
            self.communication_errors += 1
            return None
    
    async def get_data(self) -> Optional[ESP32Data]:
        """Obtener datos con cache anti-saturación"""
        try:
            current_time = time.time()
            
            # ✅ NUEVO: Usar cache para prevenir requests excesivas
            if (self._last_data and 
                (current_time - self._last_data_time) < self._cache_duration):
                logger.debug("📊 Usando datos en cache")
                return self._last_data
            
            logger.debug("📊 Solicitando datos frescos del ESP32...")
            
            # ✅ NUEVO: Timeout reducido para requests frecuentes
            response = await self._send_command("CMD:GET_DATA", timeout=3.0)
            
            if not response:
                logger.error("❌ No se recibió respuesta del ESP32")
                # ✅ NUEVO: Retornar último dato válido si existe
                if self._last_data:
                    logger.warning("⚠️ Usando último dato válido")
                    return self._last_data
                return None
            
            # Parsear respuesta
            data_dict = self._parse_data_response(response)
            if not data_dict:
                logger.error("❌ Error parseando datos del ESP32")
                return self._last_data  # ✅ Fallback a cache
            
            # Convertir a modelo Pydantic
            esp32_data = ESP32Data(**data_dict)
            
            # ✅ NUEVO: Actualizar cache
            self._last_data = esp32_data
            self._last_data_time = current_time
            
            logger.debug("✅ Datos del ESP32 obtenidos correctamente")
            return esp32_data
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos: {e}")
            # ✅ NUEVO: Retornar cache en caso de error
            if self._last_data:
                logger.warning("⚠️ Retornando datos en cache debido a error")
                return self._last_data
            return None
    
    def _parse_data_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parsear respuesta de datos del ESP32"""
        try:
            # El ESP32 envía: DATA:{json}
            if response.startswith("DATA:"):
                json_str = response[5:]  # Remover "DATA:"
                return json.loads(json_str)
            
            # O puede enviar JSON directo
            elif "{" in response:
                # Buscar el JSON en la respuesta
                start = response.find("{")
                if start != -1:
                    json_str = response[start:]
                    return json.loads(json_str)
            
            logger.error(f"❌ Formato de respuesta inválido: {response[:100]}")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            logger.error(f"   Respuesta: {response[:200]}")
            return None
    
    async def set_parameter(self, parameter: str, value: Any) -> bool:
        """Establecer un parámetro en el ESP32"""
        try:
            logger.info(f"⚙️ Configurando {parameter} = {value}")
            
            # Formatear comando según protocolo ESP32
            command = f"CMD:SET_{parameter}:{value}"
            
            # ✅ NUEVO: Timeout más largo para comandos de configuración
            response = await self._send_command(command, timeout=5.0)
            
            if response and response.startswith("OK:"):
                logger.info(f"✅ {parameter} configurado exitosamente")
                # ✅ NUEVO: Invalidar cache
                self._last_data = None
                return True
            else:
                logger.error(f"❌ Error configurando {parameter}: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción configurando {parameter}: {e}")
            return False
    
    async def toggle_load(self, total_seconds: int) -> bool:
        """Apagar carga temporalmente - COMUNICACIÓN REAL"""
        try:
            logger.info(f"🔌 Enviando comando para apagar carga por {total_seconds} segundos")
            
            command = f"CMD:TOGGLE_LOAD:{total_seconds}"
            
            # ✅ NUEVO: Timeout extra largo para acciones críticas
            response = await self._send_command(command, timeout=8.0)
            
            if response and "OK:" in response:
                logger.info(f"✅ Comando toggle_load enviado exitosamente")
                logger.info(f"   Respuesta ESP32: {response}")
                # ✅ NUEVO: Invalidar cache
                self._last_data = None
                return True
            else:
                logger.error(f"❌ Error en toggle_load: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción en toggle_load: {e}")
            return False
    
    async def cancel_temporary_off(self) -> bool:
        """Cancelar apagado temporal - COMUNICACIÓN REAL"""
        try:
            logger.info("🔌 Enviando comando para cancelar apagado temporal")
            
            command = "CMD:CANCEL_TEMP_OFF"
            
            response = await self._send_command(command, timeout=8.0)
            
            if response and "OK:" in response:
                logger.info(f"✅ Comando cancel_temporary_off enviado exitosamente")
                logger.info(f"   Respuesta ESP32: {response}")
                # ✅ NUEVO: Invalidar cache
                self._last_data = None
                return True
            else:
                logger.error(f"❌ Error en cancel_temporary_off: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción cancelando apagado: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtener información de conexión"""
        return {
            "connected": self.connected,
            "port": settings.SERIAL_PORT,
            "baudrate": settings.SERIAL_BAUDRATE,
            "last_communication": self.last_successful_communication,
            "communication_errors": self.communication_errors,
            "queue_size": 0,
            "has_cached_data": self._last_data is not None,
            "cache_age_seconds": time.time() - self._last_data_time if self._last_data else 0
        }
    
    async def stop(self):
        """Detener manager"""
        logger.info("🛑 Deteniendo ESP32 Manager...")
        
        # ✅ NUEVO: Liberar lock si está bloqueado
        try:
            if self.lock.locked():
                self.lock.release()
        except:
            pass
        
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info("✅ Puerto serial cerrado")
            except Exception as e:
                logger.error(f"❌ Error cerrando puerto serial: {e}")
        
        self.connected = False
        logger.info("✅ ESP32 Manager detenido")