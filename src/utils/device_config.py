"""
Device configuration for ML models
Automatically detects and configures GPU usage
"""

import logging
import torch

logger = logging.getLogger(__name__)


def get_optimal_device() -> str:
    """
    Detect and return the best available device
    
    Returns:
        Device string: 'cuda', or 'cpu'
    """
    
    # Check for GPU
    if torch.cuda.is_available():
        device = 'cuda'
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"GPU detected: {gpu_name}")
        logger.info(f"CUDA version: {torch.version.cuda}")
        return device
    
    
    # Fallback to CPU
    logger.warning("No GPU detected - using CPU (this will be slower)")
    logger.info("To enable GPU:")
    logger.info("  - NVIDIA: Install CUDA toolkit and PyTorch with CUDA")
    return 'cpu'
    



def get_device_info() -> dict:
    """Get detailed device information"""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    info = {
        'device': device,
        'cpu_count': torch.get_num_threads(),
        'gpu_available': torch.cuda.is_available()
    }
    
    if info['gpu_available']:
        info['gpu_count'] = torch.cuda.device_count()
        info['gpu_name'] = torch.cuda.get_device_name(0)
        info['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory / 1e9  # GB
    
    return info
    



def log_device_config():
    """Log current device configuration"""
    info = get_device_info()
    logger.info("=" * 50)
    logger.info("Device Configuration:")
    logger.info(f"  Primary Device: {info['device'].upper()}")
    logger.info(f"  CPU Threads: {info['cpu_count']}")
    
    if info['gpu_available']:
        logger.info(f"  GPU Count: {info['gpu_count']}")
        logger.info(f"  GPU Name: {info['gpu_name']}")
        logger.info(f"  GPU Memory: {info['gpu_memory']:.2f} GB")
    
    logger.info("=" * 50)


if __name__ == "__main__":
    # Test device detection
    logging.basicConfig(level=logging.INFO)
    log_device_config()
