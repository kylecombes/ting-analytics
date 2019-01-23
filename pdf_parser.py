from tabula import read_pdf
import json
import os


def parse_pdf(filename):

    if not os.path.exists(filename):
        raise FileNotFoundError('Could not find {}'.format(filename))

    templates = _load_templates()

    for template in templates:
        res = {}
        for region in template:
            area = region['area']
            pandas_options = {
                'header': region['header']
            }
            res[region['name']] = read_pdf(filename, spreadsheet=True, area=area, pandas_options=pandas_options)
        if len(res) > 0:
            return res

    return None


def _load_templates():
    template_dir = os.path.expanduser('~/ting-analytics/tabula-templates')
    template_filenames = os.listdir(template_dir)

    templates = []
    for filename in template_filenames:
        with open(os.path.join(template_dir, filename), 'r') as f:
            regions = json.load(f)
            template = []
            for r in regions:
                region = {
                    'name': r['name'],
                    'area': [r['y1'], r['x1'], r['y2'], r['x2']],
                    'header': r.get('header', 'infer')
                }
                template.append(region)
        templates.append(template)

    return templates
