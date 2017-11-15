#!/bin/python
import os, glob, fnmatch, re, sys
from os import path


def read_resources(text):
    line_list = text.split('\n')
    obj_dict = {}

    for line in line_list:
        p = line.split("=")
        if len(p) >= 2:
            key = p[0]
            value = p[1]
            obj_dict[p[0]] = p[1]

    return obj_dict

def get_font(text):
    #default: if use format {name-style-size}
    font =  text.split('-')
    idx_name = 0
    idx_style = 1
    idx_size = 2

    #if use format {name size style}
    if not (len(font) == 3):
        font =  text.split(' ')
        if not (len(font) == 3):
            print('ERROR: font format not recognized for "%s"' % text)
            print('Returning default font')
            return 'new java.awt.Font("Tahoma", java.awt.Font.PLAIN, 11)'
        idx_name = 0
        idx_style = 2
        idx_size = 1

    fstyle = re.findall('[A-Z][^A-Z]*', font[idx_style])
    lstyle = []
    for fs in fstyle:
        lstyle.append('java.awt.Font.' + fs.upper())
    return 'new java.awt.Font("' + font[idx_name] + '", ' + ' + '.join(lstyle) + ', ' +  font[idx_size] + ')'

def split_font(text):
    #default: if use format {name-style-size}
    font =  text.split('-')
    idx_name = 0
    idx_style = 1
    idx_size = 2

    #if use format {name size style}
    if not (len(font) == 3):
        font =  text.split(' ')
        if not (len(font) == 3):
            print('ERROR: font format not recognized for "%s"' % text)
            print('Returning default font')
            return ['Tahoma', '0', '11']
        idx_name = 0
        idx_style = 2
        idx_size = 1

    fstyle = re.findall('[A-Z][^A-Z]*', font[idx_style])
    lstyle = 0
    for fs in fstyle:
        if fs == 'Plain':
            lstyle += 0
        elif fs == 'Bold':
            lstyle += 1
        elif fs == 'Italic':
            lstyle += 2
    return [font[idx_name], str(lstyle),  font[idx_size]]

def split_color(text):
    lst = text.split(', ')
    out = []
    for d in lst:
        out.append(hex(int(d)).split('x')[-1])
    return out


if not len(sys.argv) > 1:
    print('usage: SAF_migrate.py path_to_saf_netbeans_project')
    sys.exit(-1)

if not os.path.isdir(sys.argv[1]):
    print('error: "%s" directory not found!' % sys.argv[1])
    print('usage: SAF_migrate.py path_to_saf_netbeans_project')
    sys.exit(-2)

root_path = sys.argv[1]

assoc_list = []

for abs_path, subdirs, files in os.walk(root_path):

    dir_list = os.listdir(abs_path)
    res_list = []

    if 'resources' in dir_list:
        print(dir_list)
        res_list = os.listdir(abs_path + '/resources')
    else:
        print('path "%s" does not contain resources dir' % abs_path)

    print('Looking for "*.form" files...')

    for file in fnmatch.filter(files, '*.form'):
        associated_files = {}
        associated_files['form'] = path.join(abs_path, file)
        print ('Found: %s' % file)
        print ('Looking for "*.java" file associated...')
        assoc_jfile = path.splitext(file)[0] + '.java'
        if  assoc_jfile in files:
            print('Found: %s' % assoc_jfile)
            associated_files['java'] = path.join(abs_path, assoc_jfile)
        else:
            print('Not java associated file found!')
        print('Looking for "*.properties" file associated...')
        assoc_pfile = (path.splitext(file)[0] + '.properties')
        if assoc_pfile in res_list:
            print('Found: %s' % assoc_pfile)
            associated_files['resources'] = path.join(abs_path + '/resources',  assoc_pfile)
        else:
            print('Not properties associated file found!')

        if 'form' in associated_files:
            assoc_list.append(associated_files)


print ('List found files\n')

for lf in assoc_list:
    if 'form' in lf:
        print('FORM: %s' % lf['form'])
    if 'java' in lf:
        print('JAVA: %s' % lf['java'])
    if 'resources' in lf:
        print('RESO: %s' % lf['resources'])
    print('\n')

print('\n')

for assoc in assoc_list:

    # processing only files with resource file associated
    if 'resources' in assoc:
        print('Processing form: "%s"...' % assoc['form'])

        f_java = open (assoc['java'], "r")
        t_java = f_java.read();
        f_java.close()

        # Read in the file
        f_form = open(assoc['form'], 'r')
        t_form = f_form.read()
        f_form.close()

        f_resources = open (assoc['resources'], "r")
        t_resources = f_resources.read();
        f_resources.close()

        res_dict = read_resources(t_resources)

        # convert form file

        t_form = re.sub(r'(.*)<Property\sname="action"\stype="javax\.swing\.Action"\seditor="org\.netbeans\.modules\.swingapp\.ActionEditor">\n.*\n(\s)*</Property>', '', t_form) #remove Action tags

        regex = re.compile(r'type="java\.lang\.String"\s(resourceKey="(.*)")')

        m = regex.search(t_form)
        while m:
            print("Found: " + m.group(1))
            print(m.group(2))
            text = m.group(1)
            key = m.group(2)
            try:
                t_form = t_form.replace(text, 'noResource="true" value="' + res_dict[key] + '"' )
            except:
                print ('Key "%s" not found' % key)
            # t_form = t_form.replace(text, 'noResource="true"')
            m = regex.search(t_form)

        regex = re.compile(r'type="javax\.swing\.Icon"\s(resourceKey="(.*)"/>)')

        m = regex.search(t_form)
        while m:
            print("Found: " + m.group(1))
            print(m.group(2))
            text = m.group(1)
            key = m.group(2)
            t_form = t_form.replace(text, 'noResource="true" editor="org.netbeans.modules.form.editors2.IconEditor">\n<Image iconType="3" name="' + res_dict[key] + '"/>\n</Property>')
            # t_form = t_form.replace(text, 'noResource="true"')
            m = regex.search(t_form)

        regex = re.compile(r'type="java\.awt\.Font"\s(resourceKey="(.*)"/>)')

        m = regex.search(t_form)
        while m:
            print("Found: " + m.group(1))
            print(m.group(2))
            text = m.group(1)
            key = m.group(2)
            style = split_font(res_dict[key])
            t_form = t_form.replace(text, 'noResource="true" editor="org.netbeans.beaninfo.editors.FontEditor">\n<Font name="'+ style[0] +'" size="'+ style[1] +'" style="'+ style[2] +'"/>\n</Property>')
            # t_form = t_form.replace(text, 'noResource="true"')
            m = regex.search(t_form)

        regex = re.compile(r'type="java\.awt\.Color"\s(resourceKey="(.*)"/>)')

        m = regex.search(t_form)
        while m:
            print("Found: " + m.group(1))
            print(m.group(2))
            text = m.group(1)
            key = m.group(2)
            rgb = split_color(res_dict[key])
            t_form = t_form.replace(text, 'noResource="true" editor="org.netbeans.beaninfo.editors.ColorEditor">\n<Color blue="'+ rgb[2] +'" green="'+ rgb[1] +'" red="'+ rgb[0] +'" type="rgb"/>\n</Property>')
            # t_form = t_form.replace(text, 'noResource="true"')
            m = regex.search(t_form)

        # convert java file
        t_java = re.sub(r'(.*)resourceMap\s=\s(.*);', '', t_java) #remove sourceMap definition
        t_java = re.sub(r'(.*)actionMap\s=\s(.*);', '', t_java) #remove actionMap definition
        t_java = re.sub(r'(.*)setAction\(actionMap\.get\("\w+"\)\);.*\n', '', t_java) #remove Actions asigns

        # change strings from resource file
        regex = re.compile(r'resourceMap\.getString\("((\w|\.)*)"\)')
        m = regex.search(t_java)
        while m:
            print("Found: " + m.group(0))
            print(m.group(1))
            text = m.group(0)
            key = m.group(1)
            try:
                t_java = t_java.replace(text, '"' + res_dict[key] + '"')
            except:
                print ('Key "%s" not found' % key)
            m = regex.search(t_java)

        # change icons from resource file
        regex = re.compile(r'resourceMap\.getIcon\("((\w|\.)*)"\)')
        m = regex.search(t_java)
        while m:
            print("Found: " + m.group(0))
            print(m.group(1))
            text = m.group(0)
            key = m.group(1)
            t_java = t_java.replace(text, 'new javax.swing.ImageIcon(getClass().getResource("' + res_dict[key] + '"))')
            m = regex.search(t_java)

        # change color from resource file
        regex = re.compile(r'resourceMap\.getColor\("((\w|\.)*)"\)')
        m = regex.search(t_java)
        while m:
            print("Found: " + m.group(0))
            print(m.group(1))
            text = m.group(0)
            key = m.group(1)
            t_java = t_java.replace(text, 'new java.awt.Color(' + res_dict[key] + ')')
            m = regex.search(t_java)

        # change fonts from resource file
        regex = re.compile(r'resourceMap\.getFont\("((\w|\.)*)"\)')
        m = regex.search(t_java)
        while m:
            print("Found: " + m.group(0))
            print(m.group(1))
            text = m.group(0)
            key = m.group(1)
            t_java = t_java.replace(text, get_font(res_dict[key]))
            m = regex.search(t_java)

        f_java = open (assoc['java'], "w")
        f_java.write(t_java)
        f_java.close()

        # Write the file out again
        with open(assoc['form'], 'w') as f_form:
          f_form.write(t_form)
          f_form.close()
