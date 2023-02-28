with open("./templates/template.py", "r") as py_file_r:
	program = py_file_r.read().replace("import images_rc", "from images import images_rc")
	with open("./templates/template.py", "w") as py_file_w:
		py_file_w.write(program)
