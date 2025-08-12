#!/usr/bin/env python3
"""
Gunicorn Configuration for ESP32 Solar Charger API
Configuración dinámica multi-arquitectura (x86/ARM/RISC-V)
"""

import multiprocessing
import os
import sys

# Agregar el directorio raíz al path para importar utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.cpu_detection import get_cached_runtime_config, get_gunicorn_config
    
    # Obtener configuración detectada
    runtime_config = get_cached_runtime_config()
    gunicorn_config = get_gunicorn_config(runtime_config)
    
    # Solo aplicar configuración si estamos en modo multi-worker
    if runtime_config["use_gunicorn"] and gunicorn_config:
        # Configuración básica de Gunicorn
        bind = gunicorn_config["bind"]
        workers = gunicorn_config["workers"]
        worker_class = gunicorn_config["worker_class"]
        worker_connections = gunicorn_config["worker_connections"]
        max_requests = gunicorn_config["max_requests"]
        max_requests_jitter = gunicorn_config["max_requests_jitter"]
        preload_app = gunicorn_config["preload_app"]
        keepalive = gunicorn_config["keepalive"]
        timeout = gunicorn_config["timeout"]
        graceful_timeout = gunicorn_config["graceful_timeout"]
        worker_tmp_dir = gunicorn_config["worker_tmp_dir"]
        
        # Configuración de logging
        accesslog = "-"
        errorlog = "-"
        loglevel = os.getenv('LOG_LEVEL', 'info').lower()
        access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
        
        # Configuración de worker
        worker_tmp_dir = "/dev/shm"
        
        # Hooks de Gunicorn
        def on_starting(server):
            server.log.info("🚀 ESP32 Solar Charger API - Iniciando con Gunicorn multi-worker")
            server.log.info(f"🏗️  Arquitectura: {runtime_config['architecture_info']['arch_type']}")
            server.log.info(f"👥 Workers: {workers}")
            server.log.info(f"⚡ Límite CPU: {runtime_config['cpu_limit']}")
            server.log.info(f"💾 Límite memoria: {runtime_config['memory_limit']}")
        
        def on_reload(server):
            server.log.info("🔄 Recargando configuración...")
        
        def worker_int(worker):
            worker.log.info(f"👷 Worker {worker.pid} interrumpido")
        
        def pre_fork(server, worker):
            server.log.info(f"👷 Iniciando worker {worker.age}")
        
        def post_fork(server, worker):
            server.log.info(f"✅ Worker {worker.pid} iniciado correctamente")
        
        def worker_abort(worker):
            worker.log.error(f"❌ Worker {worker.pid} abortado")
    
    else:
        # Fallback para modo single-worker
        print("⚠️ Modo single-worker detectado - Gunicorn no será usado")
        bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
        workers = 1
        worker_class = "uvicorn.workers.UvicornWorker"

except ImportError as e:
    print(f"⚠️ Error importando configuración de CPU: {e}")
    print("📄 Usando configuración fallback segura...")
    
    # Configuración fallback segura
    bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
    workers = 1
    worker_class = "uvicorn.workers.UvicornWorker"
    worker_connections = 1000
    max_requests = 1000
    max_requests_jitter = 50
    preload_app = True
    timeout = 30
    graceful_timeout = 30
    keepalive = 5
    accesslog = "-"
    errorlog = "-"
    loglevel = "info"

except Exception as e:
    print(f"❌ Error en configuración de Gunicorn: {e}")
    print("📄 Usando configuración mínima...")
    
    # Configuración mínima
    bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
    workers = 1
    worker_class = "uvicorn.workers.UvicornWorker"
