"""NewCrawl"""

from bibcrawl.model.postitem import PostItem
from bibcrawl.utils.priorityheuristic import PriorityHeuristic
from bibcrawl.utils.ohpython import *
from bibcrawl.utils.parsing import buildUrlFilter, parseHTML
from bibcrawl.utils.parsing import extractLinks
from scrapy.http import Request
from bibcrawl.spiders.rsscrawl import RssCrawl
from twisted.internet import reactor
from scrapy import log

class NewCrawl(RssCrawl):
  """NewCrawl"""
  name = "NewCrawl"

  def __init__(self, domain, maxDownloads=None, *args, **kwargs):
    super(NewCrawl, self).__init__(domain, *args, **kwargs)
    self.maxDownloads = maxDownloads
    self.downloadsSoFar = 0
    self.seen = set()
    self.isBlogPost = None
    self.priorityHeuristic = None

  def handleRssPosts(self, posts):
    """TODO"""
    self.isBlogPost = buildUrlFilter(imap(lambda _: _.url, posts))
    self.priorityHeuristic = PriorityHeuristic(self.isBlogPost)
    return iflatmap(lambda _: self.crawl(_), posts)

  def crawl(self, response):
    """TODO"""
    parsedBody = parseHTML(response.body)
    if self.maxDownloads and self.downloadsSoFar > self.maxDownloads:
      reactor.stop()
    elif self.isBlogPost(response.url):
      log.msg("> " + response.url, log.INFO)
      self.downloadsSoFar += 1
      yield PostItem(url=response.url, parsedBodies=(parsedBody,))

    newUrls = set(ifilter(
      lambda _: _ not in self.seen,
      extractLinks(parsedBody)))
    self.seen.update(newUrls)
    self.priorityHeuristic.feed(response.url, newUrls)
    for newUrl in newUrls:
      yield Request(
        url=newUrl,
        callback=self.crawl,
        priority=self.priorityHeuristic(newUrl))
