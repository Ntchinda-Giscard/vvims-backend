# domain/enums.py
from enum import Enum

class ReportType(str, Enum):
    VISIT = "visit"
    ATTENDANCE = "attendance"

class CategoryFilter(str, Enum):
    EMPLOYEE = "employee"
    SERVICE = "service"
    DEPARTMENT = "department"

# domain/models.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ReportRequest(BaseModel):
    report_type: ReportType
    filter_by: CategoryFilter
    filter_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ReportResponse(BaseModel):
    report_id: str
    generated_at: datetime
    report_type: ReportType
    filter_applied: CategoryFilter
    filter_details: Dict[str, str]  # Contains name and other details of filtered entity
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]

# domain/report_generator.py
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any

class ReportGenerator(ABC):
    @abstractmethod
    async def generate(self, filter_by: CategoryFilter, filter_id: str, 
                      start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        pass

class VisitReportGenerator(ReportGenerator):
    async def generate(self, filter_by: CategoryFilter, filter_id: str,
                      start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        query = self._build_query(filter_by)
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(query, filter_id, start_date, end_date)
            return [dict(row) for row in results]

    def _build_query(self, filter_by: CategoryFilter) -> str:
        base_query = """
            SELECT 
                v.visit_date,
                v.purpose,
                v.status,
        """
        
        if filter_by == CategoryFilter.EMPLOYEE:
            return base_query + """
                e.name as employee_name,
                e.employee_code,
                d.name as department_name
            FROM visits v
            JOIN employees e ON v.employee_id = e.id
            JOIN departments d ON e.department_id = d.id
            WHERE e.id = $1 AND v.visit_date BETWEEN $2 AND $3
            """
        elif filter_by == CategoryFilter.SERVICE:
            return base_query + """
                s.name as service_name,
                s.service_code,
                COUNT(*) as visit_count
            FROM visits v
            JOIN services s ON v.service_id = s.id
            WHERE s.id = $1 AND v.visit_date BETWEEN $2 AND $3
            GROUP BY s.id, v.visit_date, v.purpose, v.status
            """
        else:  # DEPARTMENT
            return base_query + """
                d.name as department_name,
                d.department_code,
                COUNT(*) as visit_count
            FROM visits v
            JOIN departments d ON v.department_id = d.id
            WHERE d.id = $1 AND v.visit_date BETWEEN $2 AND $3
            GROUP BY d.id, v.visit_date, v.purpose, v.status
            """

class AttendanceReportGenerator(ReportGenerator):
    async def generate(self, filter_by: CategoryFilter, filter_id: str,
                      start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        query = self._build_query(filter_by)
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(query, filter_id, start_date, end_date)
            return [dict(row) for row in results]

    def _build_query(self, filter_by: CategoryFilter) -> str:
        base_query = """
            SELECT 
                a.date,
                a.status,
                a.check_in,
                a.check_out,
        """
        
        if filter_by == CategoryFilter.EMPLOYEE:
            return base_query + """
                e.name as employee_name,
                e.employee_code,
                EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600 as hours_worked
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE e.id = $1 AND a.date BETWEEN $2 AND $3
            """
        elif filter_by == CategoryFilter.SERVICE:
            return base_query + """
                s.name as service_name,
                s.service_code,
                COUNT(*) as total_attendance,
                COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count
            FROM attendance a
            JOIN services s ON a.service_id = s.id
            WHERE s.id = $1 AND a.date BETWEEN $2 AND $3
            GROUP BY s.id, a.date, a.status, a.check_in, a.check_out
            """
        else:  # DEPARTMENT
            return base_query + """
                d.name as department_name,
                d.department_code,
                COUNT(*) as total_attendance,
                COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count
            FROM attendance a
            JOIN departments d ON a.department_id = d.id
            WHERE d.id = $1 AND a.date BETWEEN $2 AND $3
            GROUP BY d.id, a.date, a.status, a.check_in, a.check_out
            """

# service/report_service.py
class ReportService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.generators = {
            ReportType.VISIT: VisitReportGenerator(),
            ReportType.ATTENDANCE: AttendanceReportGenerator()
        }

    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        # Set default date range if not provided
        end_date = request.end_date or datetime.now()
        start_date = request.start_date or (end_date - timedelta(days=30))

        # Get the appropriate generator
        generator = self.generators[request.report_type]
        
        # Generate report data
        data = await generator.generate(
            request.filter_by,
            request.filter_id,
            start_date,
            end_date
        )

        # Get filter details
        filter_details = await self._get_filter_details(
            request.filter_by,
            request.filter_id
        )

        # Generate summary
        summary = self._generate_summary(request.report_type, data)

        return ReportResponse(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            report_type=request.report_type,
            filter_applied=request.filter_by,
            filter_details=filter_details,
            data=data,
            summary=summary
        )

    async def _get_filter_details(self, filter_by: CategoryFilter, filter_id: str) -> Dict[str, str]:
        tables = {
            CategoryFilter.EMPLOYEE: "employees",
            CategoryFilter.SERVICE: "services",
            CategoryFilter.DEPARTMENT: "departments"
        }
        
        async with self.db_pool.acquire() as conn:
            record = await conn.fetchrow(
                f"SELECT * FROM {tables[filter_by]} WHERE id = $1",
                filter_id
            )
            return dict(record) if record else {}

    def _generate_summary(self, report_type: ReportType, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if report_type == ReportType.VISIT:
            return {
                "total_visits": len(data),
                "completed_visits": sum(1 for d in data if d["status"] == "completed"),
                "pending_visits": sum(1 for d in data if d["status"] == "pending"),
                "cancelled_visits": sum(1 for d in data if d["status"] == "cancelled")
            }
        else:  # ATTENDANCE
            return {
                "total_days": len(data),
                "present_days": sum(1 for d in data if d["status"] == "present"),
                "absent_days": sum(1 for d in data if d["status"] == "absent"),
                "late_days": sum(1 for d in data if d["status"] == "late"),
                "average_hours": sum(d.get("hours_worked", 0) for d in data) / len(data) if data else 0
            }

# api/routes.py
from fastapi import APIRouter, Depends
from typing import Optional

router = APIRouter()

@router.post("/reports/generate")
async def generate_report(
    request: ReportRequest,
    report_service: ReportService = Depends(get_report_service)
) -> ReportResponse:
    return await report_service.generate_report(request)