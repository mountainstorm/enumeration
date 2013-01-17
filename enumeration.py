#!/usr/bin/python
# coding: latin-1

# Copyright (c) 2013 Mountainstorm
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""Python Enumerations, with ctypes support.

Typically all you need to do is produce a subclass of the 'Enumeration' class 
and add a _values_ class member.

The only member you need in your class is '_values_'.  This should be an array 
of 2-tuples; the first value of the tuple should be a string name for the 
enumeration value, the second its integer value.  If you want, you can use a 
string in place of the tuple; in this case the value is sequential from the last 
one with a value.

By default the ctype of an enumeration in c_long, and values are given integer
values starting from zero e.g. just like in C

Other class member you might want experiment with are:
* _ctype_ ; if present provides the ctype for the enumeration
* _start_value_ ; if present numbering starts from this rather than zero


For example:

class MH_FILETYPE(Enumeration):
	_ctype_ = c_uint32
	_values_ = [
		'MH_UNKNOWN',		# value is 0
		('MH_EXECUTE', 2),	# value is 2
		'MH_FVMLIB'			# value is 3
	]


To use as a defined value:
>>> MH_FILETYPE.MH_EXECUTE
2

To lookup a value's name:
>>> MH_FILETYPE[2]
MH_EXECUTE

To create an instance:
>>> a = MH_FILETYPE(MH_FILETYPE.MH_EXECUTE)

To get the name and value of a instance:
>>> a.name
MH_EXECUTE
>>> a.value
2

To test if a value is valid for the enumeration:
>>> 2 in MH_FILETYPE
True

You can also write/read them from disk (and use them within ctype structures):
>>> f = open("test", "wb+")
>>> f.write(a)
>>> f.tell()
4
>>> f.seek(0)
>>> b = MH_FILETYPE()
>>> f.readinto(b)
>>> f.tell()
4
>>> b
<value MH_EXECUTE=2 of <Enumeration MH_FILETYPE>>

Finally, you can interate over the class to see all the avaliable names:
>>> for k, v in MH_FILETYPE:
... 	print k, v
MH_UNKNOWN 0
MH_EXECUTE 2
MH_FVMLIB 3
"""


from ctypes import *
from six import with_metaclass


class EnumerationType(type(c_long)):
	def __new__(metacls, name, bases, dict):
		cls = None
		if bases[0].__name__ != "Enumeration":
			# creating a base class - just do the default construction
			cls = type(c_long).__new__(metacls, name, bases, dict)
		else:
			# creating an derivation of Enumeration - make it inherit from
			# both actual ctype we want to be, and the original base 
			# (Enumeration).  We make sure the ctype is the first parent
			# so that it overrides the parent of Enumeration (c_long)
			ctype = c_long
			if "_ctype_" in dict and dict["_ctype_"] is not c_long:
				ctype = dict["_ctype_"]
				bases = (ctype,) + bases
			cls = type(ctype).__new__(metacls, name, bases, dict)
		return cls

	def __init__(cls, name, bases, dict):
		if bases[0].__name__ == "Enumeration":
			# on init of a subclass of Enumeration fill its lookup tables
			if cls._values_ is not None:
				cls._namesByValue = {}
				cls._valuesByName = {}

				# setup start value
				start_value = 0
				if cls._start_value_ is not None:
					start_value = cls._start_value_

				# process _values_ and create the lookup dicts
				curName = None
				curValue = start_value
				for v in cls._values_:
					if isinstance(v, tuple):
						curName = v[0]
						if len(v) == 2:
							curValue = v[1]
					else:
						curName = v

					if curValue in cls._namesByValue:
						val = cls._namesByValue[curValue]
						if isinstance(val, str):
							# convert from string to tuple of strings
							cls._namesByValue[curValue] = (val, curName)
						else:
							# append additional elements to the tuple
							cls._namesByValue[curValue] = val + (curName,)
					else:
						cls._namesByValue[curValue] = curName
					cls._valuesByName[curName] = curValue
					curValue += 1

	def __contains__(cls, value):
		retVal = None
		if not (isinstance(value, str) and value.startswith("_")):
			if value in cls._namesByValue:
				retVal = cls._namesByValue[value]
		return retVal

	def __iter__(cls):
		for value in sorted(cls._namesByValue.keys()):
			name = cls._namesByValue[value]
			if isinstance(name, str):
				yield (name, value)
			else:
				for n in name:
					yield (n, value)

	def __getattr__(cls, name):
		retVal = None
		if not name.startswith("_") and "_values_" in cls.__dict__:
			if name in cls._valuesByName:
				retVal = cls._valuesByName[name]
		return retVal

	def __getitem__(cls, values):
		retVal = None
		if values in cls._namesByValue:
			retVal = cls._namesByValue[values]
		return retVal

	def __repr__(cls):
		return "<Enumeration %s>" % cls.__name__


# We derive from c_long as we need something with a _type_ member
# to keep the metaclass (derrived from c_long's type happy.  We'll override this 
# in the meta class when subclasses of Enumeration are created
class Enumeration(with_metaclass(EnumerationType, c_long)):
	def __getattr__(self, key):
		retVal = None
		if key == "name":
			retVal = self.__class__._namesByValue[self.value]
		else:
			retVal = dict.__getattr__(self, key)
		return retVal

	def __repr__(self):
		return "<value %s=%d of %r>" % (self.name, self.value, self.__class__)

	@classmethod
	def from_param(cls, param):
		retVal = None
		if isinstance(param, Enumeration):
			if param.__class__ == cls:
				retVal = param
			else:
				raise ValueError("Can't mix enumeration values")
		else:
			retVal = cls(param)
		return retVal


if __name__ == "__main__":
	class MH_FILETYPE(Enumeration):
		_ctype_ = c_uint32
		_values_ = [
			'MH_UNKNOWN',		# value is 0
			('MH_EXECUTE', 2),	# value is 2
			'MH_FVMLIB'			# value is 3
		]

	print((MH_FILETYPE.MH_EXECUTE))
	print((MH_FILETYPE[2]))
	a = MH_FILETYPE(MH_FILETYPE.MH_EXECUTE)
	print((a.name))
	print((a.value))
	print((2 in MH_FILETYPE))
	f = open("test", "wb+")
	f.write(a)
	print((f.tell()))
	f.seek(0)
	b = MH_FILETYPE()
	f.readinto(b)
	print((f.tell()))
	print(b)
	for k, v in MH_FILETYPE:
		print((k, v))





