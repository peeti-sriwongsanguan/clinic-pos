from setuptools import setup, find_packages

setup(
    name="beauty-clinic-pos",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'pillow>=10.2.0',
        'ttkthemes>=3.2.2',
        'reportlab>=4.0.8',
        'python-dotenv>=1.0.1',
        'SQLAlchemy>=2.0.27',
        'pandas>=2.2.0',
        'numpy>=1.26.4',
        'bcrypt>=4.1.2',
        'PyJWT>=2.8.0',
        'cryptography>=42.0.2',
        'python-dateutil>=2.8.2',
        'qrcode>=7.4.2',
        'validate-email>=1.3',
        'phonenumbers>=8.13.30',
        'python-barcode>=0.15.1',
    ],
    python_requires='>=3.10',
)