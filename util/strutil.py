import logging
log = logging.getLogger('strutil')

from enforce_typing import enforce_types # type: ignore[import]
import inspect

@enforce_types
class StrMixin(object):
    
    def __str__(self) -> str:
        class_name = self.__class__.__name__

        newline = False
        if hasattr(self, '__STR_GIVES_NEWLINE__'):
            newline = self.__STR_GIVES_NEWLINE__ # type: ignore [attr-defined]
        
        s = []
        s += ["%s={" % class_name]
        if newline: s += ["\n"]

        obj = self

        short_attrs, long_attrs = [], []
        for attr in dir(obj):
            if '__' in attr: continue
            attr_obj = getattr(obj, attr)
            if inspect.ismethod(attr_obj): continue
            if isinstance(attr_obj, int) or isinstance(attr_obj, float) or \
               (attr_obj is None) or isinstance(attr_obj, str):
                short_attrs.append(attr)
            else:
                long_attrs.append(attr)
        attrs = short_attrs + long_attrs #print short attrs first
        
        for i, attr in enumerate(attrs): 
            attr_obj = getattr(obj, attr)
            s += ["%s=" % attr]
            if isinstance(attr_obj, dict):
                s += [dictStr(attr_obj, newline)]
            else:
                s += [str(attr_obj)]

            if i < (len(attrs)-1):
                s += [","]
            s += [" "]
            if newline: s += ["\n"]

        s += ["/%s}" % class_name]
        return "".join(s)
    
@enforce_types
def dictStr(d : dict, newline=False) -> str:
    if not d:
        return "{}"
    s = ["dict={"]
    for i,(k,v) in enumerate(d.items()):
        s += ["'%s':%s" % (k, v)]
        if i < (len(d)-1):
            s += [","]
        s += [" "]
        if newline: s += ["\n"]
    s += ["/dict}"]
    return "".join(s)

def asCurrency(amount, decimals:bool=True) -> str:
    """Ref: https://stackoverflow.com/questions/21208376/converting-float-to-dollars-and-cents"""
    if decimals:
        if amount >= 0:
            return '${:,.2f}'.format(amount)
        else:
            return '-${:,.2f}'.format(-amount)
    else:
        if amount >= 0:
            return '${:,.0f}'.format(amount)
        else:
            return '-${:,.0f}'.format(-amount)

def prettyBigNum(amount, remove_zeroes:bool=True) -> str:
    """Prints, for example:
    1.23e12, 123.4B, 1.23B, 123M, 1.23M, 123K, 1.23K, 123,
    1.23, 0.12, 1.23e-3,
    1e12, 100B, 1B, 100M, 1M, 100K, 1K, 100, 1 

    Remove zeros True vs False: 1.00M vs 1M
    """
    if remove_zeroes:
        amount = float('%.2e' % amount) #reduce to 3 sig figs
    if amount == 0:
        return "0"
    
    a = abs(amount)

    if a >= 1e12 or a < 1e-1:
        s = format(a, '.2e').replace("e+", "e").replace('e0','e').replace('e-0','e-')
        base = 'e'
        s = s.replace('e','X')
    elif a >= 1e9:
        s = '%.2fX' % (a/1e9)
        base = 'B'
    elif a >= 1e6:
        s = '%.2fX' % (a/1e6)
        base = 'M'
    elif a >= 1e3:
        s = '%.2fX' % (a/1e3)
        base = 'K'
    else:
        s = '%.2fX' % a
        base = ''

    if remove_zeroes:
        s = s.replace('0X','X').replace('.0X','X')
        
    s = s.replace('X', base)
            
    if amount < 0:
        s = "-" + s
        
    return s
        
