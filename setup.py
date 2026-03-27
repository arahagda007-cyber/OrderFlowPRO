
---

## **ARCHIVO 6: setup.py** (opcional - para instalación)
```python
from setuptools import setup, find_packages

setup(
    name="OrderFlowPRO",
    version="2.0.0",
    author="Tu Nombre",
    description="Sistema de Gestión de Pedidos y Ventas",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tuusuario/OrderFlowPRO",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "orderflowpro=orderflow_pro:main",
        ],
    },
)