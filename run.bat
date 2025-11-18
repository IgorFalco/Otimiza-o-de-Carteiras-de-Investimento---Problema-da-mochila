@echo off
REM Sistema de Otimização de Carteiras - B3

echo.
echo ========================================
echo  Sistema de Otimizacao de Carteiras
echo ========================================
echo.

set GRB_LICENSE_FILE=C:\Users\igort\gurobi.lic

call .venv\Scripts\activate.bat

python main.py

deactivate
