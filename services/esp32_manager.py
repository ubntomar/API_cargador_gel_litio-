#!/usr/bin/env python3
"""
ESP32Manager - Comunicación Serial Real con ESP32
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
        
    async def start(self) -> bool:
        """Inicializar manager y conectar"""
        logger.info("🚀 Iniciando ESP32 Manager con comunicación real...")
        
        if await self._connect():
            logger.info("✅ ESP32 Manager iniciado correctamente")
            return True
        
        logger.error("❌ Error iniciando ESP32 Manager")
        return False
    
    async def _connect(self) -> bool:
        """Establecer conexión serial"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔌 Intento {attempt + 1}: Conectando a {settings.SERIAL_PORT}")
                
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
                
                # Probar comunicación enviando GET_DATA
                if await self._test_communication():
                    self.connected = True
                    self.communication_errors = 0
                    logger.info(f"✅ Conectado al ESP32 en {settings.SERIAL_PORT}")
                    return True
                else:
                    logger.warning(f"❌ No se pudo comunicar con ESP32 en intento {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"❌ Intento {attempt + 1} falló: {e}")
                await asyncio.sleep(1)
        
        self.connected = False
        return False
    
    async def _test_communication(self) -> bool:
        """Probar comunicación con el ESP32"""
        try:
            logger.info("🧪 Probando comunicación con ESP32...")
            
            # Enviar comando de prueba
            response = await self._send_command("CMD:GET_DATA")
            
            if response and (response.startswith("DATA:") or "panelToBatteryCurrent" in response):
                logger.info("✅ Comunicación con ESP32 exitosa")
                return True
            else:
                logger.warning(f"⚠️ Respuesta inesperada del ESP32: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando comunicación: {e}")
            return False
    
    async def _send_command(self, command: str, timeout: float = 5.0) -> Optional[str]:
        """Enviar comando al ESP32 y obtener respuesta"""
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("❌ Puerto serial no está abierto")
            return None
        
        try:
            with self.lock:
                logger.debug(f"📤 Enviando: {command}")
                
                # Limpiar buffer de entrada
                self.serial_conn.reset_input_buffer()
                
                # Enviar comando
                command_bytes = (command + '\n').encode('utf-8')
                self.serial_conn.write(command_bytes)
                self.serial_conn.flush()
                
                # Leer respuesta con timeout
                start_time = time.time()
                response = ""
                
                while (time.time() - start_time) < timeout:
                    if self.serial_conn.in_waiting > 0:
                        try:
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
                                        
                        except UnicodeDecodeError:
                            logger.warning("⚠️ Error decodificando respuesta")
                            continue
                    
                    await asyncio.sleep(0.01)  # No bloquear completamente
                
                logger.warning(f"⏰ Timeout esperando respuesta para: {command}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error enviando comando '{command}': {e}")
            self.communication_errors += 1
            return None
    
    async def get_data(self) -> Optional[ESP32Data]:
        """Obtener datos completos del ESP32"""
        try:
            logger.debug("📊 Solicitando datos del ESP32...")
            
            response = await self._send_command("CMD:GET_DATA")
            
            if not response:
                logger.error("❌ No se recibió respuesta del ESP32")
                return None
            
            # Parsear respuesta
            data_dict = self._parse_data_response(response)
            if not data_dict:
                logger.error("❌ Error parseando datos del ESP32")
                return None
            
            # Convertir a modelo Pydantic
            esp32_data = ESP32Data(**data_dict)
            logger.debug("✅ Datos del ESP32 obtenidos correctamente")
            return esp32_data
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos: {e}")
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
            
            response = await self._send_command(command)
            
            if response and response.startswith("OK:"):
                logger.info(f"✅ {parameter} configurado exitosamente")
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
            
            # Comando según protocolo ESP32: TOGGLE_LOAD:{seconds}
            command = f"CMD:TOGGLE_LOAD:{total_seconds}"
            
            response = await self._send_command(command, timeout=10.0)
            
            if response and "OK:" in response:
                logger.info(f"✅ Comando toggle_load enviado exitosamente")
                logger.info(f"   Respuesta ESP32: {response}")
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
            
            response = await self._send_command(command, timeout=10.0)
            
            if response and "OK:" in response:
                logger.info(f"✅ Comando cancel_temporary_off enviado exitosamente")
                logger.info(f"   Respuesta ESP32: {response}")
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
            "queue_size": 0
        }
    
    async def stop(self):
        """Detener manager"""
        logger.info("🛑 Deteniendo ESP32 Manager...")
        
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info("✅ Puerto serial cerrado")
            except Exception as e:
                logger.error(f"❌ Error cerrando puerto serial: {e}")
        
        self.connected = False
        logger.info("✅ ESP32 Manager detenido")