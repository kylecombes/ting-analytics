from tabula import read_pdf
import json
import os


def parse_pdf(filename, template_dir=None):
    if not os.path.exists(filename):
        raise FileNotFoundError('Could not find {}'.format(filename))

    if template_dir is None:
        template_dir = os.path.dirname(filename)

    templates = _load_templates(template_dir)

    for idx, template in enumerate(templates):
        res = {}
        for region in template:
            area = region['area']
            pandas_options = {
                'header': region['header']
            }
            res[region['name']] = read_pdf(filename, spreadsheet=True, area=area, pandas_options=pandas_options)

        # Check if parsing was successful with this template
        if res and res['summary'] is not None and res['usage'] is not None and len(res['summary'].index) == 3 and len(res['usage'].index) >= 4 and \
                __get_nan_count(res['summary']) == 0 and __get_nan_count(res['usage']) == 0:
            res['template-used'] = idx
            return res

    return None


def __get_nan_count(df):
    return int(df.isna().sum().get(0))


def _load_templates(template_dir):
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
