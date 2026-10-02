"""Read the evidence Core already persisted; never validate/consume another start."""
import json

from session.session_boundary import FileIdentity


def consumed_start_evidence(dialogue):
    authority_path = dialogue.boundary.directory / 'session_start_authority.json'
    record = json.loads(authority_path.read_text(encoding='utf-8'))
    reference = FileIdentity(**record['consumption_ref'])
    reference.validate()
    return reference
