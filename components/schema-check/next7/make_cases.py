"""Fixed before results: baseline cases, 42 original Suite groups, typed lifts and controls."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
cases=json.loads((P/'BASE-CASES.json').read_text())
for c in cases:c['scope']='old-original-80' if c['kind'] in ['suite-original','next3-suite-original'] else 'old-other'
numeric=['minimum','maximum','exclusiveMinimum','exclusiveMaximum','multipleOf']
for f in sorted((P/'sources').glob('*.json')):
    if f.stem=='MANIFEST':continue
    for i,g in enumerate(json.loads(f.read_text())):
        name=f'suite7-{f.stem}-{i}'
        cases.append({'id':name,'kind':'new-suite-original','scope':'new-original-42','schema':g['schema'],'tests':g['tests']})
        if f.stem in numeric:
            for typ in ['number','integer']:
                schema={'allOf':[{'type':typ},g['schema']]}
                tests=[{**t,'valid':t['valid'] and type(t['data'])in [int,float] and (typ=='number' or t['data']==int(t['data']))} for t in g['tests']]
                cases.append({'id':name+'-typed-'+typ,'kind':'explicit-type-lift','scope':'new-typed-lifts','schema':schema,'tests':tests})
def add(name,s,tests):cases.append({'id':name,'kind':'next7-development','scope':'new-controls','schema':s,'tests':[{'data':x,'valid':v} for x,v in tests]})
add('number-finite-tenths',{'type':'number','minimum':-0.3,'maximum':0.3,'multipleOf':0.1},[(0.3,True),(-0.3,True),(0.31,False),(True,False)])
add('number-exclusive-empty',{'type':'number','minimum':0,'exclusiveMaximum':0},[(0,False),(-0.1,False),(1,False)])
add('integer-fractional-window-empty',{'type':'integer','exclusiveMinimum':0,'maximum':0.5},[(0,False),(0.5,False),(1,False)])
add('integer-multiple-rational',{'type':'integer','multipleOf':1.5},[(3,True),(-3,True),(1,False),(1.5,False),(0,True)])
add('number-unbounded-decimal',{'type':'number','minimum':-1.25,'exclusiveMaximum':2.5},[(-1.25,True),(2.499,True),(2.5,False),(-1.251,False),(True,False)])
add('number-oneof-divisibility',{'type':'number','oneOf':[{'multipleOf':0.2},{'multipleOf':0.3}]},[(0.2,True),(0.3,True),(0.6,False),(0,False),(0.1,False)])
add('array-boolean-bounded',{'type':'array','items':{'type':'boolean'},'minItems':1,'maxItems':2},[([],False),([True],True),([False,True],True),([False,False,False],False),([1],False)])
add('array-unique-finite',{'type':'array','items':{'enum':[True,1,1.0,False]},'uniqueItems':True},[([],True),([True,1,False],True),([1,1.0],False),([True,1],True),([False,0],False)])
add('array-unique-impossible',{'type':'array','items':{'enum':[0,1]},'minItems':3,'uniqueItems':True},[([0,1,0],False),([],False)])
add('array-items-false',{'type':'array','items':False},[([],True),([1],False)])
add('array-length-empty',{'type':'array','items':{'type':'boolean'},'minItems':2,'maxItems':1},[([],False),([True],False),([True,False],False)])
add('array-rational-items',{'type':'array','items':{'type':'number','minimum':0,'maximum':0.3,'multipleOf':0.1},'maxItems':2,'uniqueItems':True},[([0.1,0.3],True),([0.3,0.3],False),([0.31],False),([],True)])
add('array-nested-finite',{'type':'array','items':{'type':'array','items':{'type':'boolean'},'maxItems':1},'maxItems':2},[([[],[True]],True),([[False,True]],False),([True],False)])
add('object-rational-array',{'type':'object','properties':{'a':{'type':'array','items':{'const':0.1},'maxItems':2}},'required':['a'],'additionalProperties':False},[({'a':[0.1]},True),({'a':[0.2]},False),({},False)])
add('unsupported-open-array',{'type':'array','maxItems':1},[([],True),([[[]]],True)])
add('unsupported-infinite-unique',{'type':'array','items':{'type':'number'},'uniqueItems':True},[([1,2],True),([1,1],False)])
(P/'CASES.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n');print(len(cases))
