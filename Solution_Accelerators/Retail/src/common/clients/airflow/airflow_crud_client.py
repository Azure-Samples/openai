import uuid
from datetime import datetime
from common.clients.airflow.http_client import HTTPClient

# ToDo: Cleanup before merge, add error handling.
class AirflowCRUD(HTTPClient):
    def __init__(self, base_uri, logger, username, password):
        super().__init__(base_uri, logger)
        self.auth = (username, password)
    
    def get_dags(self, limit: int = 100, only_active: bool = True):
        path = f"/api/v1/dags?limit={limit}&only_active={only_active}"
        json_response, _ = self.make_request(path, self.HttpMethod.GET, auth=self.auth)
        return json_response
    
    def get_dag(self, dag_id: str):
        path = f"/api/v1/dags/{dag_id}"
        json_response, _ = self.make_request(path, self.HttpMethod.GET, auth=self.auth)
        return json_response
    
    def trigger_dag(self, dag_id: str, conf: dict = None):
        path = f"/api/v1/dags/{dag_id}/dagRuns"
        current_time = datetime.utcnow()
        formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        body = {
            "conf": conf,
            "dag_run_id": uuid.uuid4().hex,
            "logical_date": formatted_time,
            "note": ""
        }
        json_response, _ = self.make_request(path, self.HttpMethod.POST, auth=self.auth, payload=body)
        return json_response
    
    def get_dag_run(self, dag_id: str, dag_run_id: str):
        path = f"/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"
        json_response, _ = self.make_request(path, self.HttpMethod.GET, auth=self.auth)
        return json_response