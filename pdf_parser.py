from tabula import read_pdf
import json
import os


def parse_pdf(filename, template=None):

    if not os.path.exists(filename):
        raise FileNotFoundError('Could not find {}'.format(filename))

    if template:
        template = _load_template(template)

        res = {}
        for region in template:
            area = region['area']
            pandas_options = {
                'header': region['header']
            }
            res[region['name']] = read_pdf(filename, spreadsheet=True, area=area, pandas_options=pandas_options)

    else:
        res = read_pdf(filename)

    return res


def _load_template(filename):
    with open(filename, 'r') as f:
        templates = json.load(f)
        res = []
        for t in templates:
            region = {
                'name': t['name'],
                'area': [t['y1'], t['x1'], t['y2'], t['x2']],
                'header': t.get('header', 'infer')
            }
            res.append(region)
        return res
