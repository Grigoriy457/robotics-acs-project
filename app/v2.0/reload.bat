@echo off
python -m PyQt5.uic.pyuic -x "./templates/template.ui" -o "./templates/template.py"
"templates/reload.py"
pyrcc5 "./images/images.qrc" -o "./images/images_rc.py"
python -m PyQt5.uic.pyuic -x "./templates/dialog_template.ui" -o "./templates/dialog_template.py"
pause
