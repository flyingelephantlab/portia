from collections import OrderedDict
from urllib2 import URLError, HTTPError

from django.core.exceptions import ValidationError
from django.http.response import Http404

import requests

from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from django.conf import settings

from .projects import BaseProjectModelRoute, ProjectDownloadMixin
from ..jsonapi.exceptions import JsonApiGeneralException
from ..utils.extract import Pages, load_spider, FetchError
from ..utils.train import train_scrapely
from ..utils.cookies import CookiesFetcher
from portia_server import settings
from portia_orm.models import Spider


class SpiderRoute(ProjectDownloadMixin, BaseProjectModelRoute):


  scrapyjob = {}
  lookup_url_kwarg = 'spider_id'
  lookup_value_regex = '[^/]+'
  default_model = Spider

  def get_instance(self):
    return self.get_collection()[self.kwargs.get('spider_id')]

  def get_collection(self):
    return self.project.spiders

  @detail_route(methods=['post'])
  def extract(self, *args, **kwargs):
    try:
      instance = self.get_instance()
    except TypeError:
      raise JsonApiGeneralException(
        'No spider found with the name "%s"' % kwargs.get('spider_id'),
        404)
    try:
      spider = load_spider(self.storage, instance)
    except (ValueError, KeyError, IndexError):
      raise JsonApiGeneralException(
        'Failed to load spider, "%s" correctly' % instance.id, 500)
    pages = self._build_pages(spider)
    try:
      data = pages.extract_items()
    except FetchError as e:
      raise JsonApiGeneralException(e.message, e.status)
    return Response(data, status=HTTP_200_OK)

  def _build_pages(self, spider):
    return Pages(self.data, spider)

  @detail_route(methods=['post'])
  def rename(self, *args, **kwargs):
    try:
      spider = self.get_instance()
      name = self.data['name']
      self.project.spiders
      possible_spider = Spider(self.storage, id=name)
      if possible_spider in self.project.spiders and name != spider.id:
        raise JsonApiGeneralException(
          'Spider already exists in this project with the name, '
          '"%s"' % name, HTTP_400_BAD_REQUEST)
      spider.id = name
      spider.save()
      self.storage.commit()
    except (TypeError, IndexError, KeyError):
      raise Http404

    data = self.get_serializer(spider).data
    return Response(data, status=HTTP_200_OK)

  @detail_route(methods=['post'])
  def start_crawl(self, *args, **kwargs):
    try:
      instance = self.get_instance()
    except TypeError:
      raise JsonApiGeneralException(
        'No spider found with the name "%s"' % kwargs.get('spider_id'), 404)
    merchant_name = instance.id
    merchant_country = instance.country_code
    scheduele_request = 'http://{}:{}@{}?project={}&spider={}&merchant_name={}&merchant_country={}'.format(
      settings.SCRAPYD_USERNAME, settings.SCRAPYD_PASSWORD, settings.SCHEDULE_URL,
      settings.KIPP_DEFAULT_PROJECT, settings.KIPP_PORTIA_SPIDER, merchant_name, merchant_country)
    request = requests.post(scheduele_request)
    self.scrapyjob[instance.id] = request.json()['jobid']
    if request.status_code != 200:
      raise JsonApiGeneralException(
        request.status_code, request.content)
    else:
      schedueled = '{} crawling started'.format(merchant_name)
    return Response(schedueled, status=HTTP_200_OK)

  @detail_route(methods=['post'])
  def cancel_crawl(self, *args, **kwargs):
    try:
      instance = self.get_instance()
    except TypeError:
      raise JsonApiGeneralException(
        'No spider found with the name "%s"' % kwargs.get('spider_id'), 404)
    merchant_name = instance.id
    cancel_request = 'http://{}:{}@{}?project={}&jobid={}'.format(
      settings.SCRAPYD_USERNAME, settings.SCRAPYD_PASSWORD, settings.CANCEL_SCHEDUELE_URL,
      settings.KIPP_DEFAULT_PROJECT, self.scrapyjob[instance.id])
    request = requests.post(cancel_request)
    print request.reason
    if request.status_code != 200:
      raise JsonApiGeneralException(
        request.status_code, request.content)
    else:
      schedueled = '{} crawling stopped'.format(merchant_name)
    return Response(schedueled, status=HTTP_200_OK)



  @detail_route(methods=['post'])
  def train(self, *args, **kwargs):
    try:
      instance = self.get_instance()
    except TypeError:
      raise JsonApiGeneralException(
        'No spider found with the name "%s"' % kwargs.get('spider_id'), 404)
    username = self.data['data'].get('username')
    if not username:
      raise JsonApiGeneralException('Invalid username', 400)
    try:
      templates = train_scrapely(self.storage, instance, username)
    except ValidationError, e:
      raise JsonApiGeneralException(e.message, 400)
    return Response(templates, status=HTTP_200_OK)

  @detail_route(methods=['post'])
  def cookies(self, *args, **kwargs):
    try:
      current_url = self.data['current_url']
    except KeyError:
      return Response("Missing 'current_url' in payload", status=HTTP_400_BAD_REQUEST)
    fetcher = CookiesFetcher()
    try:
      cookies = fetcher.fetch(current_url)
    except(ValueError, TypeError, URLError, HTTPError) as e:
      raise JsonApiGeneralException(e.message, 400)
    return Response(cookies, status=HTTP_200_OK)
