# from pdf2image import convert_from_path
# import nbformat as nbf
# import sys
# import os
#
# nb = nbf.v4.new_notebook()
# # print(os.path.splitext(sys.argv[1])[0])
#
# pdf_filename = os.path.basename(sys.argv[1])
#
# dir_path = os.path.splitext(sys.argv[1])[0]
# os.mkdir(dir_path)
# dir_name = os.path.splitext(pdf_filename)[0]
#
# slide_list = convert_from_path(str(sys.argv[1]))
# cell_list = []
# i = 1
# for slide in slide_list:
#     slide_str = "slide" + str(i)
#     slide.save(dir_path + "/" + slide_str + ".png", "PNG")
#     i = i + 1
#     path = '''"''' + "./" + dir_name + "/" + slide_str + ".png" + '''"'''
#     text = "<img src=" + path + ' height="600" width="700" />'
#     cell_list.append(nbf.v4.new_markdown_cell(text))
#
# nb["cells"] = cell_list
#
# nb_filename = os.path.splitext(pdf_filename)[0] + ".ipynb"
#
# nbf.write(nb, os.path.dirname(dir_path) + "/" + nb_filename)

