import os
import json
import shutil

from django.core.exceptions import ValidationError
import logging
from storage.projecttemplates import MERCHANT_SETTING_BASE
from git import Repo


KIPP_SETTINGS_REPO = '/app/kipp_settings'
KIPP_MERCHANT_SETTINGS_DIR = '/app/kipp_settings/{country_code}/{spider_name}'
PORTIA_DATA_DIR_BASE = '/app/slyd/slyd/data/projects/yaoota'
PORTIA_SPIDERS_DIR = '/app/slyd/slyd/data/projects/yaoota/spiders'
PORTIA_SPIDER_TEMPLATES = '/app/slyd/slyd/data/projects/yaoota/spiders/{spider_name}'


def train_scrapely(storage, model, username):
    """
    Train scrapely function
    :param storage:
    :param model:
    :return:
    """
    merchant_settings = create_kipp_setting(model)
    save_kipp_config(spider_name=model.id, country_code=model.country_code, merchant_settings=merchant_settings)
    save_portia_spider(spider_name=model.id, country_code=model.country_code)
    publish_kipp_settings(username=username, country_code=model.country_code, spider_name=model.id)


def generate_scrapely_templates(templates):
    """
    Combine all templates in a list and add headers
    :param templates:
    :return: scrapely_templates: a list of all templates for this spider
    """
    scrapely_templates = []
    for template in templates:
        scrapely_template = dict()
        scrapely_template['url'] = template.get('url', '')
        scrapely_template['headers'] = template.get('headers', {})
        scrapely_template['encoding'] = template.get('encoding', 'utf-8')
        scrapely_template['body'] = template.get('annotated_body', '')
        scrapely_template['page_id'] = template.get('page_id', '')
        scrapely_templates.append(scrapely_template.copy())
    return scrapely_templates


def save_portia_spider(spider_name, country_code):
    """
    Copy portia data for spider specified from data folder to kipp settings
    :param spider_name:
    :param country_code:
    :return:
    """
    def copytree(src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    os.makedirs(d)
                copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    kipp_merchant_settings_dir = KIPP_MERCHANT_SETTINGS_DIR.format(country_code=country_code, spider_name=spider_name)
    merchant_init_path = os.path.join(kipp_merchant_settings_dir, '__init__.py')
    if not os.path.exists(kipp_merchant_settings_dir):
        os.makedirs(kipp_merchant_settings_dir)
        with open(merchant_init_path, mode='w') as f:
            f.write("/n")

    portia_spider_name = "%s.json" % spider_name
    portia_spider_file = os.path.join(PORTIA_SPIDERS_DIR, portia_spider_name)
    merchant_file_path = os.path.join(kipp_merchant_settings_dir, portia_spider_name)
    shutil.copyfile(portia_spider_file, merchant_file_path)
    portia_spider_templates = PORTIA_SPIDER_TEMPLATES.format(spider_name=spider_name)
    merchant_templates = os.path.join(kipp_merchant_settings_dir, "templates")
    if not os.path.exists(merchant_templates):
        os.makedirs(merchant_templates)
    copytree(portia_spider_templates, merchant_templates)


def save_scrapely_object(spider_name, country_code, scrapely_templates):
    """
    SaSaving spider configuration file for kipp on disk
    :param spider_name:
    :param country_code:
    :param scrapely_templates:
    :return:
    """
    kipp_merchant_settings_dir = KIPP_MERCHANT_SETTINGS_DIR.format(country_code=country_code, spider_name=spider_name)
    if not os.path.exists(kipp_merchant_settings_dir):
        os.makedirs(kipp_merchant_settings_dir)
    scrapely_file_name = "%s.json" % spider_name
    scrapely_file_path = os.path.join(kipp_merchant_settings_dir, scrapely_file_name)
    with open(scrapely_file_path, "w") as outfile:
        json.dump({"templates": scrapely_templates}, outfile)
    logging.log(logging.INFO,'Scrapely Scraper instance is saved at %s' % kipp_merchant_settings_dir)


def save_kipp_config(spider_name, country_code, merchant_settings):
    """
    Saving spider configuration file for kipp on disk
    :param spider_name:
    :param country_code:
    :param username:
    :param merchant_settings:
    :return:
    """
    kipp_merchant_settings_dir = KIPP_MERCHANT_SETTINGS_DIR.format(country_code=country_code, spider_name=spider_name)
    if not os.path.exists(kipp_merchant_settings_dir):
        os.makedirs(kipp_merchant_settings_dir)
    merchant_file_name = "%s_ai.py" % spider_name
    merchant_file_path = os.path.join(kipp_merchant_settings_dir, merchant_file_name)
    with open(merchant_file_path, 'w') as f:
        f.write(merchant_settings)
    logging.log(logging.INFO,'%s kipp configurations is saved at %s'.format(spider_name, kipp_merchant_settings_dir))


def create_kipp_setting(spider):
    """
    preprocess spider specs and generate kipp settings file
    :param merchant_name:
    :param country:
    :param spider_spec:
    :return:
    """
    setting_dict = {
        'merchant_name': spider.id,
        'country_code': spider.country_code,
        'currency_code': spider.currency_code,
        'allow_regex': spider.follow_patterns,
        'deny_regex': spider.exclude_patterns,
        'local_images': spider.local_images,
        'render_js': spider.js_enabled,
        'english_language_cookie': None,
        'arabic_language_cookie': None,
        'currency_cookie': None,
        'general_cookie': None,
        'english_cookie_name': spider.english_cookie_name,
        'english_cookie_value': spider.english_cookie_value,
        'arabic_cookie_name': spider.arabic_cookie_name,
        'arabic_cookie_value': spider.arabic_cookie_value,
        'currency_cookie_name': spider.currency_cookie_name,
        'currency_cookie_value': spider.currency_cookie_value,
        'use_language_config': spider.use_language_config,
        'use_currency_config': spider.use_currency_config,
    }

    try:
        start_urls = spider.start_urls[0]['url']
        allowed_domains = [start_urls.split("//")[-1].split("/")[0].replace("www.", "")]
    except IndexError:
        raise ValidationError(message="start url is missing or not valid")

    setting_dict['start_urls'] = [start_urls]
    setting_dict['merchant_url'] = start_urls
    setting_dict['allowed_domains'] = allowed_domains

    setting_dict['english_url'] = "\"%s\"" % spider.english_url if spider.english_url else None
    setting_dict['arabic_url'] = "\"%s\"" % spider.arabic_url if spider.arabic_url else None
    setting_dict['english_url_args'] = "\"%s\"" % spider.english_url_args if spider.english_url_args else None
    setting_dict['arabic_url_args'] = "\"%s\"" % spider.arabic_url_args if spider.arabic_url_args else None

    if spider.use_language_cookies:
        setting_dict['english_language_cookie'] = """
                    {{'name':"{english_cookie_name}", 'value': "{english_cookie_value}",
                    'domain': ".{allowed_domains[0]}", 'path': '/'}}
                    """.format(**setting_dict)
        setting_dict['arabic_language_cookie'] = """
                    {{'name': "{arabic_cookie_name}", 'value': "{arabic_cookie_value}",
                    'domain': '.{allowed_domains[0]}', 'path': '/'}}
                    """.format(**setting_dict)

    if spider.use_currency_cookies:
        setting_dict['currency_cookie'] = """
                    {{'name':"{currency_cookie_name}", 'value': "{currency_cookie_value}",
                    'domain': ".{allowed_domains[0]}", 'path': '/'}}
                    """.format(**setting_dict)

    if spider.use_language_cookies and spider.use_currency_cookies:
        setting_dict['general_cookie'] = """
                    [{}, {}]
                    """.format(setting_dict['english_language_cookie'], setting_dict['currency_cookie'])
    elif spider.use_language_cookies:
        setting_dict['general_cookie'] = """
                    [{}]
                    """.format(setting_dict['english_language_cookie'])

        if setting_dict['english_language_cookie']:
            setting_dict['english_language_cookie'] = "[%s]" % setting_dict['english_language_cookie']

        if setting_dict['arabic_language_cookie']:
            setting_dict['arabic_language_cookie'] = "[%s]" % setting_dict['arabic_language_cookie']

    elif setting_dict['currency_cookie']:
        setting_dict['general_cookie'] = """
                    [{}]
                    """.format(setting_dict['currency_cookie'])
        setting_dict['currency_cookie'] = [setting_dict['currency_cookie']]

    if setting_dict["use_language_config"]:
        localization_template = """{{
                  'english': {{
                      'url': {english_url},
                      'cookie_config': {english_language_cookie},
                      'url_args': {english_url_args}
                  }},
                  'arabic': {{
                      'url': {arabic_url},
                      'cookie_config': {arabic_language_cookie},
                      'url_args': {arabic_url_args}
                  }}
              }}
          """.format(**setting_dict)
    else:
        localization_template = None

    setting_dict['localization_template'] = localization_template

    merchant_setting = MERCHANT_SETTING_BASE.format(**setting_dict)
    return merchant_setting


def publish_kipp_settings(username, country_code, spider_name):
    """
    Commit and push configuration files
    :param username:
    :param country_code:
    :param spider_name:
    :return:
    """

    kipp_country_setting_dir = KIPP_MERCHANT_SETTINGS_DIR.format(username=username,
                                                                 country_code=country_code,
                                                                 spider_name=spider_name)
    kipp_config_file_path = os.path.join(kipp_country_setting_dir, '%s_ai.py' % spider_name)
    portia_config_file_path = os.path.join(kipp_country_setting_dir, '/%s.json' % spider_name)
    temlate_dir = os.path.join(kipp_country_setting_dir, "templates")
    if os.path.exists(kipp_config_file_path) and os.path.exists(portia_config_file_path):
        #TODO: try and catch exceptions
        repo = Repo(KIPP_SETTINGS_REPO)
        config = repo.config_writer()
        config.set_value("user", "name", username)
        index = repo.index
        index.add([kipp_config_file_path, portia_config_file_path, temlate_dir])
        commit_msg = '%s: Update %s[%s] spider configurations' % (username, spider_name, country_code)
        index.commit(commit_msg)
        origins = repo.remotes
        #TODO: Handling git username and password
        origins[0].push()
