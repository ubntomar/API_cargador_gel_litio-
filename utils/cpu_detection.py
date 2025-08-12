#!/usr/bin/env python3
"""
CPU Detection and Configuration Utilities
Detección automática de CPU y configuración óptima para multi-arquitecturas
"""

import os
import multiprocessing
import platform
import subprocess
from typing import Dict, Tuple, Any
from core.logger import logger

class CPUDetector:
    """Detector de configuración óptima de CPU para cualquier arquitectura"""
    
    def __init__(self):
        self.cpu_count = multiprocessing.cpu_count()
        self.architecture = platform.machine().lower()
        self.system = platform.system().lower()
        
    def get_architecture_info(self) -> Dict[str, Any]:
        """Obtener información detallada de la arquitectura"""
        try:
            arch_info = {
                "cpu_count": self.cpu_count,
                "architecture": self.architecture,
                "system": self.system,
                "platform": platform.platform(),
                "processor": platform.processor() or "unknown"
            }
            
            # Detectar tipo específico de arquitectura
            if "x86" in self.architecture or "amd64" in self.architecture:
                arch_info["arch_type"] = "x86_64"
            elif "arm" in self.architecture or "aarch64" in self.architecture:
                arch_info["arch_type"] = "arm"
            elif "riscv" in self.architecture or "risc" in self.architecture:
                arch_info["arch_type"] = "riscv"
            else:
                arch_info["arch_type"] = "unknown"
            
            return arch_info
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando arquitectura: {e}")
            return {
                "cpu_count": self.cpu_count,
                "architecture": "unknown",
                "system": "unknown",
                "arch_type": "unknown"
            }
    
    def detect_optimal_workers(self, max_workers_env: str = "auto") -> int:
        """
        Detectar número óptimo de workers basado en:
        - Número de CPUs disponibles
        - Arquitectura del sistema
        - Variables de entorno
        - Requerimientos del puerto serial
        """
        try:
            # Si se especifica un número manual, usarlo
            if max_workers_env.isdigit():
                manual_workers = int(max_workers_env)
                logger.info(f"🔧 Usando workers manuales: {manual_workers}")
                return max(1, min(manual_workers, 8))  # Límite seguro
            
            # Auto-detección inteligente
            if max_workers_env.lower() == "auto":
                optimal = self._calculate_optimal_workers()
                logger.info(f"🤖 Workers auto-detectados: {optimal} (CPUs: {self.cpu_count}, Arch: {self.architecture})")
                return optimal
            
            # Fallback seguro
            logger.warning(f"⚠️ Valor inválido para MAX_WORKERS: {max_workers_env}, usando auto-detección")
            return self._calculate_optimal_workers()
            
        except Exception as e:
            logger.error(f"❌ Error detectando workers óptimos: {e}")
            return 1  # Fallback ultra-seguro
    
    def _calculate_optimal_workers(self) -> int:
        """Calcular workers óptimos basado en hardware disponible"""
        try:
            # Reglas adaptativas por número de CPUs
            if self.cpu_count <= 1:
                return 1  # Single-core: solo 1 worker
            elif self.cpu_count == 2:
                return 1  # Dual-core: 1 worker para dejar recursos al sistema
            elif self.cpu_count <= 4:
                return 2  # Quad-core: 2 workers
            elif self.cpu_count <= 6:
                return 3  # 6-core: 3 workers
            elif self.cpu_count <= 8:
                return 4  # 8-core: 4 workers
            else:
                return min(6, self.cpu_count - 2)  # Muchos cores: máximo 6, dejar 2 libres
                
        except Exception as e:
            logger.error(f"❌ Error calculando workers: {e}")
            return 1
    
    def detect_optimal_cpu_limit(self, cpu_limit_env: str = "auto") -> str:
        """Detectar límite óptimo de CPU para Docker"""
        try:
            # Si se especifica manual, usarlo
            if cpu_limit_env != "auto" and cpu_limit_env.replace(".", "").isdigit():
                manual_limit = float(cpu_limit_env)
                logger.info(f"🔧 Usando límite de CPU manual: {manual_limit}")
                return f"{min(manual_limit, self.cpu_count):.1f}"
            
            # Auto-detección
            if cpu_limit_env.lower() == "auto":
                optimal = self._calculate_optimal_cpu_limit()
                logger.info(f"🤖 Límite de CPU auto-detectado: {optimal} (CPUs totales: {self.cpu_count})")
                return optimal
            
            # Fallback
            logger.warning(f"⚠️ Valor inválido para CPU_LIMIT: {cpu_limit_env}, usando auto-detección")
            return self._calculate_optimal_cpu_limit()
            
        except Exception as e:
            logger.error(f"❌ Error detectando límite de CPU: {e}")
            return "2.0"  # Fallback seguro
    
    def _calculate_optimal_cpu_limit(self) -> str:
        """Calcular límite óptimo de CPU"""
        try:
            # Dejar al menos 1 CPU libre para el sistema
            if self.cpu_count <= 2:
                return "1.0"
            elif self.cpu_count <= 4:
                return f"{self.cpu_count - 1}.0"
            elif self.cpu_count <= 8:
                return f"{self.cpu_count - 1}.0"
            else:
                # Para sistemas con muchos cores, usar máximo 6-8 CPUs
                return f"{min(8, self.cpu_count - 2)}.0"
                
        except Exception as e:
            logger.error(f"❌ Error calculando límite de CPU: {e}")
            return "2.0"
    
    def detect_optimal_memory(self, memory_env: str = "auto") -> str:
        """Detectar límite óptimo de memoria"""
        try:
            # Si se especifica manual, usarlo
            if memory_env != "auto":
                logger.info(f"🔧 Usando límite de memoria manual: {memory_env}")
                return memory_env
            
            # Auto-detección basada en número de workers
            workers = self.detect_optimal_workers()
            
            # Memoria base + escalado por workers
            base_memory = 512  # MB
            worker_memory = 256  # MB por worker adicional
            
            total_memory = base_memory + (worker_memory * max(0, workers - 1))
            
            # Límites seguros
            total_memory = min(total_memory, 2048)  # Max 2GB
            total_memory = max(total_memory, 256)   # Min 256MB
            
            result = f"{total_memory}m"
            logger.info(f"🤖 Memoria auto-detectada: {result} (Workers: {workers})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error detectando memoria: {e}")
            return "512m"  # Fallback seguro

def get_runtime_config() -> Dict[str, Any]:
    """
    Obtener configuración de runtime completa
    
    Esta función es llamada al inicio de la aplicación para
    determinar la configuración óptima del sistema.
    """
    detector = CPUDetector()
    
    # Obtener variables de entorno
    max_workers_env = os.getenv('MAX_WORKERS', 'auto')
    cpu_limit_env = os.getenv('CPU_LIMIT', 'auto')
    memory_limit_env = os.getenv('MEMORY_LIMIT', 'auto')
    force_single_worker = os.getenv('FORCE_SINGLE_WORKER', 'false').lower() == 'true'
    
    # Detectar configuración óptima
    arch_info = detector.get_architecture_info()
    optimal_workers = detector.detect_optimal_workers(max_workers_env)
    optimal_cpu_limit = detector.detect_optimal_cpu_limit(cpu_limit_env)
    optimal_memory = detector.detect_optimal_memory(memory_limit_env)
    
    # Forzar single worker si es necesario (para debugging o compatibilidad)
    if force_single_worker:
        optimal_workers = 1
        logger.warning("⚠️ FORCE_SINGLE_WORKER activado - usando 1 worker")
    
    config = {
        "architecture_info": arch_info,
        "workers": optimal_workers,
        "cpu_limit": optimal_cpu_limit,
        "memory_limit": optimal_memory,
        "use_gunicorn": optimal_workers > 1,
        "single_worker_mode": optimal_workers == 1,
        "env_values": {
            "MAX_WORKERS": max_workers_env,
            "CPU_LIMIT": cpu_limit_env,
            "MEMORY_LIMIT": memory_limit_env,
            "FORCE_SINGLE_WORKER": force_single_worker
        }
    }
    
    # Log de configuración detectada
    logger.info("🔍 =================== CONFIGURACIÓN DE CPU DETECTADA ===================")
    logger.info(f"🏗️  Arquitectura: {arch_info['arch_type']} ({arch_info['architecture']})")
    logger.info(f"🔧 CPUs totales: {arch_info['cpu_count']}")
    logger.info(f"👥 Workers: {optimal_workers}")
    logger.info(f"⚡ Límite CPU: {optimal_cpu_limit}")
    logger.info(f"💾 Límite memoria: {optimal_memory}")
    logger.info(f"🚀 Modo: {'Gunicorn multi-worker' if config['use_gunicorn'] else 'Uvicorn single-worker'}")
    logger.info("🔍 ====================================================================")
    
    return config

def get_gunicorn_config(runtime_config: Dict[str, Any]) -> Dict[str, Any]:
    """Generar configuración específica para Gunicorn"""
    if not runtime_config["use_gunicorn"]:
        return {}
    
    workers = runtime_config["workers"]
    
    gunicorn_config = {
        "bind": f"0.0.0.0:{os.getenv('PORT', 8000)}",
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "worker_connections": 1000,
        "max_requests": 2000,
        "max_requests_jitter": 100,
        "preload_app": True,
        "keepalive": 5,
        "timeout": 30,
        "worker_tmp_dir": "/dev/shm",  # Usar memoria compartida
        "graceful_timeout": 30,
        "max_requests_jitter": 50,
    }
    
    # Configuración específica por arquitectura
    arch_type = runtime_config["architecture_info"]["arch_type"]
    
    if arch_type == "riscv":
        # RISC-V puede necesitar timeouts más largos
        gunicorn_config["timeout"] = 45
        gunicorn_config["graceful_timeout"] = 45
    elif arch_type == "arm":
        # ARM puede ser más lento en algunas operaciones
        gunicorn_config["timeout"] = 35
    
    logger.info(f"🔧 Configuración Gunicorn generada para {workers} workers ({arch_type})")
    
    return gunicorn_config

# Variables globales para uso en main.py
_runtime_config = None

def get_cached_runtime_config() -> Dict[str, Any]:
    """Obtener configuración de runtime (con cache)"""
    global _runtime_config
    if _runtime_config is None:
        _runtime_config = get_runtime_config()
    return _runtime_config
