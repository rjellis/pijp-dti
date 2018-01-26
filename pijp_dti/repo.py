import csv
import getpass
from datetime import datetime

from pijp.repositories import BaseRepository
from pijp import dbprocs
from pijp.dbprocs import format_string_parameter as fsp

PROCESS_NAME = 'pijp-dti'


class DTIRepo(BaseRepository):
    def __init__(self):
        super().__init__()
        self.connection.setdb('imaging')

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
        WHERE st.StudyCode = {project} 
            AND SeriesDescription LIKE '%MR 2D AXIAL DTI BRAIN%'
        """.format(project=fsp(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_staged_cases(self, project):

        sql = r"""
        SELECT
            ScanCode AS Code
        From 
            ProcessingLog
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'Stage'
            AND (Outcome = 'Done' or Outcome = 'Error')
        """.format(project=fsp(project), process=fsp(PROCESS_NAME))

        todo = self.connection.fetchall(sql)
        return todo

    def get_masks_to_qc(self, project):
        sql = r"""
        SELECT DISTINCT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE Project = {0}
            AND Process = {1}
            AND Step = 'RoiStats'
            AND Outcome = 'Done'
            AND ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE Project = {0}
                    AND Process = {1}
                    AND Step = 'MaskQC'
                    AND (Outcome = 'Pass' OR Outcome = 'Edit')
            )
        """.format(dbprocs.format_string_parameter(project), fsp(PROCESS_NAME))

        todo = self.connection.fetchall(sql)
        return todo

    def get_segs_to_qc(self, project):
        sql = r"""
        SELECT
            ScanCode AS Code
        FROM 
            ProcessingLog
        WHERE Project = {0}
            AND Process = {1}
            AND Step = 'MaskQC'
            AND Outcome = 'Pass'
            AND ScanCode NOT IN(
                SELECT
                    ScanCode
                FROM
                    ProcessingLog
                WHERE Project = {0}
                AND Process = {1}
                AND Step = 'SegQC'
                AND (Outcome = 'Pass' OR Outcome = 'Fail')
            )
        """.format(dbprocs.format_string_parameter(project), fsp(PROCESS_NAME))

        sql2 = r"""
        SELECT
            ScanCode AS Code
        FROM
            ProcessingLog
        WHERE Project = {0}
            AND Process = {1}
            AND Step = 'RoiStats'
            AND Outcome = 'Redone'
            AND ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog
                WHERE Project = {0}
                AND Process = {1}
                AND Step = 'SegQC'
                AND (Outcome = 'Pass' OR Outcome = 'Fail')
            )
        """.format(fsp(project), fsp(PROCESS_NAME))  # Need this second query for getting redone edited cases

        todo = self.connection.fetchall(sql)
        todo2 = self.connection.fetchall(sql2)

        return todo + todo2

    def get_warps_to_qc(self, project):
        sql = r"""
        SELECT
            ScanCode AS Code
        FROM 
            ProcessingLog
        WHERE Project = {0}
            AND Process = {1}
            AND Step = 'SegQC'
            AND Outcome = 'Pass'
            AND ScanCode NOT IN(
                SELECT
                    ScanCode
                FROM
                    ProcessingLog
                WHERE Project = {0}
                AND Process = {1}
                AND Step = 'WarpQC'
                AND (Outcome = 'Pass' OR Outcome = 'Fail')
            )
        """.format(dbprocs.format_string_parameter(project), fsp(PROCESS_NAME))

        todo = self.connection.fetchall(sql)
        return todo

    def is_edited(self, project, code):
        sql = r"""
        SELECT
            ScanCode
        FROM
            ProcessingLog
        WHERE
            ScanCode = {code}
            AND Project = {project}
            AND Process = {process}
            AND Step = 'MaskQC'
            AND Outcome = 'edit'
        """.format(code=fsp(code), project=fsp(project), process=fsp(PROCESS_NAME))

        edited = self.connection.fetchone(sql)
        return edited is not None  # Returns true if edited, false if not edited

    def get_edited_masks(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE Project = {0}
            AND Process = {1}
            AND Step = 'MaskQC'
            AND Outcome = 'edit'
            AND ScanCode NOT IN(
                SELECT
                    ScanCode
                FROM
                    ProcessingLog
                WHERE Project = {0}
                AND Process = {1}
                AND Step = 'ApplyMask'
                AND Outcome = 'Redone'
            )
        """.format(dbprocs.format_string_parameter(project), fsp(PROCESS_NAME))

        todo = self.connection.fetchall(sql)
        return todo

    def set_roi_stats(self, project_id, code, md, fa, ga, rd, ad):
        sql = r"""
        INSERT INTO pijp_dti (Code, ProjectID, FileName, Measure, Roi, MinVal, MaxVal, MeanVal, StdDev, MedianVal, 
                              Volume, RecordDate)
        VALUES ({code}, {project_id}, {fname}, {measure}, {roi}, {min}, {max}, {mean}, {sd}, {median}, {vol}, {time})
        """
        measures = [md, fa, ga, rd, ad]
        for m in measures:
            with open(m) as csvfile:
                mreader = csv.reader(csvfile, delimiter=',')
                msr = fsp(m.split('_')[-2].rstrip('_roi.csv'))  # fsp() : dbprocs.format_string_parameters
                for row in mreader:
                    if mreader.line_num == 1:
                        row.pop()
                    else:
                        fname = fsp(m.split('/')[-1])
                        roi = fsp(str(row[0]))
                        min_val = fsp(str(row[1]))
                        max_val = fsp(str(row[2]))
                        mean_val = fsp(str(row[3]))
                        sd = fsp(str(row[4]))
                        median_val = fsp(str(row[5]))
                        volume = fsp(str(row[6]))
                        time = fsp(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        formatted_sql = sql.format(code=fsp(code), project_id=project_id, fname=fname, measure=msr,
                                                   roi=roi, min=min_val, max=max_val, mean=mean_val, sd=sd,
                                                   median=median_val, vol=volume, time=time)
                        self.connection.execute_non_query(formatted_sql)

    def remove_roi_stats(self, project, code):
        project_id = self.get_project_id(project)
        sql = r"""
        DELETE FROM pijp_dti WHERE ProjectID = {0} AND Code = {1} 
        """.format(project_id['ProjectID'], fsp(code))

        self.connection.execute_non_query(sql)

    def get_project_id(self, project):
        sql = r"""
        SELECT ProjectID FROM Projects WHERE ProjectName = {0}
        """.format(fsp(project))

        project_id = self.connection.fetchone(sql)
        return project_id

    def find_where_left_off(self, project, step):

        sql = r"""
        SELECT ScanCode as Code, Outcome, Comments
        FROM ProcessingLog
        WHERE Project = {project}
        AND Step = {step} 
        AND CompletedBy = {user} 
        ORDER BY CompletedOn DESC
        """.format(project=fsp(project), step=fsp(step), user=fsp(getpass.getuser()))

        left_off = self.connection.fetchone(sql)
        return left_off
