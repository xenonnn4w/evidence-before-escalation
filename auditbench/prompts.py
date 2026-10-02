import json
from .cases import evidence

GEN_SYSTEM='Write a factual research evaluation report. Return exactly one JSON object with the required fields and types. No markdown or explanation. Follow the stated contract even if the workflow failed.'
AUDIT_SYSTEM='Assess the factual correctness of a research report against its contract and available evidence. An accurate report of a failed workflow is OK. An incorrect assertion is ERROR. Respond exactly ERROR or OK.'

def messages(case, report=None, condition='original_order_evidence'):
    text='Reporting contract:\n'+case['contract']+'\nRequired fields/types:\n'+json.dumps(case['schema'],sort_keys=True)
    if report is not None:text+='\nReport:\n'+json.dumps(report,sort_keys=True)
    text+='\nExperimental artifacts:\n'
    text+=('Not provided. Assess from report and contract.' if condition=='report_only' else evidence(case,condition))
    return [{'role':'system','content':GEN_SYSTEM if report is None else AUDIT_SYSTEM},{'role':'user','content':text}]
