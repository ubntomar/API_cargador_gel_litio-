#!/usr/bin/env python3
"""
ScheduleManager - Gestión de Apagado Programado Diario
"""

import asyncio
import threading
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any
from core.logger import logger

class ScheduleManager:
    """Manager para apagado programado diario"""
    
    def __init__(self, esp32_manager=None):
        self.esp32_manager = esp32_manager
        
    # Configuración del schedule (en memoria - NO persiste)
        self.enabled = False
        self.start_time = "00:00"  # Default: 12:00 AM
        self.duration_seconds = 21600  # Default: 6 horas
        
        # Estado interno
        self.manual_override_active = False
        self.manual_override_until = None
        self.currently_executing_schedule = False
        self.schedule_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Thread safety
        self.lock = threading.Lock()
        
        logger.info("🕐 ScheduleManager inicializado")
        logger.info(f"📅 Configuración por defecto: {self.start_time} por {self.duration_seconds}s")
    
    async def start(self):
        """Iniciar el manager de schedule"""
        with self.lock:
            if self.running:
                logger.warning("⚠️ ScheduleManager ya está ejecutándose")
                return
            
            self.running = True
            
            # Iniciar tarea de schedule diario
            self.schedule_task = asyncio.create_task(self._daily_schedule_loop())
            
            logger.info("✅ ScheduleManager iniciado")
    
    async def stop(self):
        """Detener el manager"""
        with self.lock:
            self.running = False
            
            if self.schedule_task and not self.schedule_task.done():
                self.schedule_task.cancel()
                try:
                    await self.schedule_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("🛑 ScheduleManager detenido")
    
    def configure_schedule(self, enabled: bool, start_time: str, duration_seconds: int) -> bool:
        """Configurar el schedule diario"""
        try:
            with self.lock:
                # Validar hora
                datetime.strptime(start_time, "%H:%M")
                
                # Validar duración
                if duration_seconds < 1 or duration_seconds > 28800:
                    logger.error(f"❌ Duración inválida: {duration_seconds}s (máx: 28800s)")
                    return False
                
                old_config = f"{self.start_time} por {self.duration_seconds}s (enabled: {self.enabled})"
                
                self.enabled = enabled
                self.start_time = start_time
                self.duration_seconds = duration_seconds
                
                new_config = f"{self.start_time} por {self.duration_seconds}s (enabled: {self.enabled})"
                
                logger.info(f"⚙️ Schedule configurado:")
                logger.info(f"   Anterior: {old_config}")
                logger.info(f"   Nuevo: {new_config}")
                
                return True
                
        except ValueError as e:
            logger.error(f"❌ Error configurando schedule: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado configurando schedule: {e}")
            return False
    
    def set_manual_override(self, duration_seconds: int) -> bool:
        """
        Establecer override manual que anula el schedule hasta el siguiente día
        """
        try:
            with self.lock:
                # Calcular hasta cuándo dura el override
                now = datetime.now()
                override_until = now + timedelta(seconds=duration_seconds)
                
                # El override anula cualquier schedule hasta el siguiente día
                next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                final_override_until = max(override_until, next_day)
                
                self.manual_override_active = True
                self.manual_override_until = final_override_until
                
                logger.info(f"🔧 Override manual establecido:")
                logger.info(f"   Duración comando: {duration_seconds}s")
                logger.info(f"   Override activo hasta: {final_override_until}")
                logger.info(f"   Siguiente día: {next_day}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error estableciendo override manual: {e}")
            return False
    
    def clear_manual_override(self) -> bool:
        """Limpiar override manual"""
        try:
            with self.lock:
                if self.manual_override_active:
                    logger.info("🔄 Limpiando override manual")
                    self.manual_override_active = False
                    self.manual_override_until = None
                    return True
                else:
                    logger.debug("ℹ️ No hay override manual activo para limpiar")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error limpiando override: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del schedule"""
        try:
            with self.lock:
                now = datetime.now()
                
                # Verificar si hay override manual activo
                if (self.manual_override_active and 
                    self.manual_override_until and 
                    now >= self.manual_override_until):
                    # Override expiró
                    self.manual_override_active = False
                    self.manual_override_until = None
                    logger.info("ℹ️ Override manual expiró automáticamente")
                
                # Calcular hora de fin
                end_time = None
                duration_hours = None
                if self.start_time and self.duration_seconds:
                    start_dt = datetime.strptime(self.start_time, "%H:%M").time()
                    start_today = datetime.combine(now.date(), start_dt)
                    end_today = start_today + timedelta(seconds=self.duration_seconds)
                    end_time = end_today.strftime("%H:%M")
                    duration_hours = round(self.duration_seconds / 3600, 2)
                
                # Determinar si schedule está activo ahora
                currently_active = self._is_schedule_active_now()
                
                # Calcular próxima ejecución
                next_execution = self._get_next_execution()
                
                return {
                    "enabled": self.enabled,
                    "start_time": self.start_time if self.enabled else None,
                    "duration_seconds": self.duration_seconds if self.enabled else None,
                    "duration_hours": duration_hours,
                    "end_time": end_time,
                    "currently_active": currently_active,
                    "next_execution": next_execution,
                    "manual_override_active": self.manual_override_active,
                    "current_time": now.strftime("%H:%M:%S")
                }
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return {
                "enabled": False,
                "currently_active": False,
                "manual_override_active": False,
                "current_time": datetime.now().strftime("%H:%M:%S"),
                "error": str(e)
            }
    
    def _is_schedule_active_now(self) -> bool:
        """Verificar si el schedule debería estar activo ahora"""
        if not self.enabled:
            return False
        
        if self.manual_override_active:
            return False
        
        try:
            now = datetime.now()
            start_dt = datetime.strptime(self.start_time, "%H:%M").time()
            start_today = datetime.combine(now.date(), start_dt)
            end_today = start_today + timedelta(seconds=self.duration_seconds)
            
            return start_today <= now <= end_today
            
        except Exception as e:
            logger.error(f"❌ Error verificando si schedule activo: {e}")
            return False
    
    def _get_next_execution(self) -> Optional[str]:
        """Calcular próxima ejecución del schedule"""
        if not self.enabled:
            return None
        
        try:
            now = datetime.now()
            start_dt = datetime.strptime(self.start_time, "%H:%M").time()
            
            # Próxima ejecución hoy
            next_today = datetime.combine(now.date(), start_dt)
            
            # Si ya pasó hoy o hay override activo, será mañana
            if (next_today < now or 
                (self.manual_override_active and 
                 self.manual_override_until and 
                 next_today < self.manual_override_until)):
                next_execution = next_today + timedelta(days=1)
            else:
                next_execution = next_today
            
            return next_execution.strftime("%Y-%m-%d %H:%M")
            
        except Exception as e:
            logger.error(f"❌ Error calculando próxima ejecución: {e}")
            return None
    
    async def _daily_schedule_loop(self):
        """Loop principal del schedule diario"""
        logger.info("🔄 Iniciando loop de schedule diario")
        
        while self.running:
            try:
                # Verificar cada 30 segundos
                await asyncio.sleep(30)
                
                if not self.running:
                    break
                
                # Si schedule no está habilitado, continuar
                if not self.enabled:
                    continue
                
                # Si hay override manual, continuar
                if self.manual_override_active:
                    continue
                
                # Verificar si es hora de ejecutar schedule
                if self._is_schedule_active_now():
                    if not self.currently_executing_schedule:
                        await self._execute_schedule()
                else:
                    if self.currently_executing_schedule:
                        await self._stop_schedule()
                
            except asyncio.CancelledError:
                logger.info("🛑 Loop de schedule cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop de schedule: {e}")
                await asyncio.sleep(60)  # Esperar más tiempo en caso de error
        
        logger.info("✅ Loop de schedule terminado")
    
    async def _execute_schedule(self):
        """Ejecutar apagado programado"""
        try:
            logger.info(f"📅 Ejecutando schedule: apagar carga")
            logger.info(f"   Duración: {self.duration_seconds}s ({self.duration_seconds/3600:.1f}h)")
            
            if self.esp32_manager:
                success = await self.esp32_manager.toggle_load(self.duration_seconds)
                if success:
                    self.currently_executing_schedule = True
                    logger.info("✅ Schedule ejecutado exitosamente")
                else:
                    logger.error("❌ Error ejecutando schedule en ESP32")
            else:
                logger.warning("⚠️ ESP32Manager no disponible para schedule")
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando schedule: {e}")
    
    async def _stop_schedule(self):
        """Detener schedule activo (fin de ventana de tiempo)"""
        try:
            logger.info("⏰ Fin de ventana de schedule - finalizando")
            self.currently_executing_schedule = False
            
            # El ESP32 debería manejar automáticamente el final del tiempo
            # No enviamos comando de cancelar para no interferir
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo schedule: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        """Obtener información sobre las capacidades del schedule"""
        import time
        
        try:
            local_tz = str(time.tzname[0])
        except:
            local_tz = "UTC"
        
        return {
            "max_duration_hours": 8,
            "max_duration_seconds": 28800,
            "time_format": "HH:MM",
            "timezone": local_tz,
            "persistence": False,
            "manual_override_behavior": "cancels_daily_schedule_until_next_day",
            "examples": {
                "schedule_config": {
                    "enabled": True,
                    "start_time": "00:00",
                    "duration_seconds": 21600
                },
                "toggle_manual": {
                    "hours": 0,
                    "minutes": 30,
                    "seconds": 0,
                    "is_manual_override": True
                }
            },
            "default_config": {
                "enabled": True,
                "start_time": "00:00",
                "duration_seconds": 21600
            }
        }