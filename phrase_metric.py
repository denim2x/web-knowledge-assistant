# -*- coding: utf-8 -*-
import re
from collections import namedtuple

from pattern.en import parsetree
from pattern.en.wordnet import _pattern2wordnet as _pos, wn_ic, wn, WordNetSynset as Synset
from pattern.text.tree import Text, Sentence, Chunk, Word

from util import mixin, mean, casefold

# Rationale: {Egypt} ~ {Egyptian} > {Tennessee} ~ {Egyptian}
IC_CORPUS = wn_ic.ic('ic-shaks.dat')
_lemmata = False

def _parse(*args, **kw):  # FIXME (workaround)
  from pattern.text.en import parser
  if isinstance(parser.model, str):
    from pattern.text import Model
    parser.model = Model(path=parser.model)

  return parsetree(*args, **kw)

def _casefold(text):
  return { casefold(text), casefold(getattr(text, 'lemma', text)) }

def _similar(a, b):
  return bool(_casefold(a) & _casefold(b))

def _ratio(*data):
  _len = [len(e) for e in data]
  return mean(_len) / max(_len)

def _mean(data, threshold=0, default=0):
  return mean((e for e in data if e > threshold), default)

def _min(data, threshold=0, default=0):
  return min((e for e in data if e > threshold), default=default)

@mixin(Synset)
class _Synset:
  def similarity(self, other):
    if self._pos != other._pos:
      return None
    if self._pos in 'asr':
      return self.wup_similarity(other)
    return self.jcn_similarity(other, IC_CORPUS)
    
@mixin(Word)
class _Word:
  def synsets(self, type=None):
    return wn.synsets(str(self), _pos.get(type[:2] if type else None))

  def _similarity(self, other, default=0):
    #s = sorted((other.similarity(s) or default for s in self.synsets()), default=default)
    #return max((other.similarity(s) or default for s in self.synsets()), default=default)
    return (other.similarity(s) or default for s in self.synsets())

  def similarity(self, other, default=0):
    if isinstance(other, Chunk):
      return max((self.similarity(w) for w in other), default=default)
    if isinstance(other, Synset):
      return max(self._similarity(other), default=default)
      #return self._similarity(other)

    if self.type == other.type and _similar(self, other):
      return 1
    return max(self._similarity(other), default=default)
    #return self._similarity(other)

Factor = namedtuple('Factor', ('factor', 'value'))

@mixin(Chunk)
class _Chunk:
  factors = dict(VP=0.07, ADJP=0.02, ADVP=0.01)

  @property
  def nouns(self):
    if not hasattr(self, '_nouns'):
      nouns = [w for w in self if w.type[:2] == 'NN']
      self._nouns = Chunk(self.sentence, nouns, self.type, self.role, self.relation)
    return self._nouns

  @property
  def main(self):
    return self.type == 'NP'

  def _related(self, other, type, scaling):
    factor = self.factors[type]
    a, b = (e.nearest(type) for e in (self, other))
    if None in {a, b}:
      return Factor(0, 0)
    return Factor(factor, a._similarity(b, scaling))

  def similarity(self, other, value=None, scaling=True):
    if value is None:
      return self._similarity(other, scaling)

    related = [self._related(other, type, scaling) for type in self.factors]
    factor = 1 - sum(e.factor for e in related)

    return factor * value + sum(e.factor * e.value for e in related)

  @property
  def lemma(self):
    if not hasattr(self, '_lemma'):
      self._lemma = ' '.join(e for e in self.lemmata if e)
    return self._lemma

  def _similarity(self, other, scaling, default=0):
    if self.type == other.type and _similar(self, other):
      return 1
    ratio = _ratio(self, other) if scaling else 1
    return _mean((w.similarity(other) for w in self), default=0) * ratio

@mixin(Sentence)
class _Sentence:
  @property
  def noun_phrases(self):
    if not hasattr(self, '_noun'):
      self._noun = [p for p in self.phrases if p.nouns and p.main]
    return self._noun

  @property
  def main_phrases(self):
    if not hasattr(self, '_main'):
      self._main = [p for p in self.phrases if p.main]
    return self._main

@mixin(Text)
class _Text:
  def __new__(cls, self, lemmata=True):
    if self is None:
      return self
    if not isinstance(self, Text):
      if isinstance(self, list):
        self = '\n'.join(e for e in self if e)
      self = _parse(self, lemmata=lemmata and _lemmata)
    return self

  @property
  def noun_phrases(self):
    if not hasattr(self, '_noun'):
      self._noun = [p for s in self for p in s.noun_phrases]
    return self._noun

  @property
  def main_phrases(self):
    if not hasattr(self, '_main'):
      self._main = [p for s in self for p in s.main_phrases]
    return self._main


def validate(self):
  return bool(_Text(self).noun_phrases)


def similarity(a, b, scaling='inner', split=5):
  """Computes a non-negative score representing the amount of common information between a and b"""
  X, Y = (_Text(e) for e in (a, b))
  if casefold(X) == casefold(Y):
    return 1
  A, B = (e.noun_phrases for e in (X, Y))
  data = []
  scaling = 'total' if scaling is True else scaling
  inner = scaling in { 'inner', 'total' }
  for a in A:
    S = sorted(((a.similarity(b, scaling=inner), b) for b in B), key=lambda e: e[0], reverse=True)
    m = max((a.similarity(p, s, scaling=inner) for (s, p) in S[:split]), default=0)
    _len = len(S)
    if _len > split:
      f = max([len(S[split:]) / _len, 0.3])
      data.append(m * (1 - f) + S[split][0] * f)
    else:
      data.append(m)

  ratio = _ratio(A, B) if scaling in { 'outer', 'total' } else 1
  return _mean(data) * ratio


def distance(a, b):
  return 1 - similarity(a, b)


for i in range(5):   # FIXME (workaround)
  try:
    _parse('sample text', lemmata=True)
    _lemmata = True
    break
  except (RuntimeError, ValueError):
    pass

