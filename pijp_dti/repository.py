from pijp.repositories import BaseRepository
from pijp import dbprocs


class DTIRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self.connection.setdb('imaging')

    def get_step_queue(self, project, process, step):
            sql = r"""
            SELECT 
            ScanCode AS Code
            FROM 
            ProcessingLog pl 
            WHERE Project = {project} 
            AND Process = {process}
            AND Step = {prev_step_name}
            AND (Outcome = 'Done' OR Outcome = 'pass')
            AND ScanCode NOT IN (SELECT 
            ScanCode
            FROM 
            ProcessingLog pl 
            WHERE Project = {project} 
            AND Process = {process} 
            AND Step = {step_name}
            AND (Outcome = 'Done' OR Outcome = 'pass'))
            
            """.format(project=dbprocs.format_string_parameter(project),
                       process=dbprocs.format_string_parameter(process),
                       step_name=dbprocs.format_string_parameter(step.step_name),
                       prev_step_name=dbprocs.format_string_parameter(step.prev_step[0].step_name))

            ready = self.connection.fetchall(sql)
            return ready

    def get_mask_qc_list(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE 
            Project = {0}
        AND 
            Process = 'dti' 
        AND 
            Step = 'Preregister'
        AND 
            Outcome = 'Done'
        AND 
            ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE 
                    Project = {0}
                AND 
                    Process = 'dti' 
                AND 
                    Step = 'MaskQC'
                AND 
                    Outcome = 'pass'
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_warp_qc_list(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE 
            Project = {0}
        AND 
            Process = 'dti' 
        AND 
            Step = 'TensorFit'
        AND 
            Outcome = 'Done'
        AND 
            ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE 
                    Project = {0}
                AND 
                    Process = 'dti' 
                AND 
                    Step = 'WarpQC'
                AND 
                    Outcome = 'pass'
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_project_dtis(self, project):

        sql = r"""
        SELECT 
            SeriesCode AS Code
        FROM 
            dbo.DicomSeries se
        INNER JOIN
            dbo.DicomStudies st
        ON
            se.StudyInstanceUID = st.StudyInstanceUID
        WHERE 
            st.StudyCode = {project} 
        AND 
            SeriesDescription LIKE '%MR 2D AXIAL DTI BRAIN%'
        """.format(project=dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo
