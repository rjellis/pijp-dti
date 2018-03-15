import os
import csv
import getpass
from datetime import datetime

from pijp.core import get_project_dir
from pijp.dbprocs import format_string_parameter as fsp
from pijp.repositories import BaseRepository

import pijp_dti

PROCESS_TITLE = pijp_dti.__process_title__


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
            AND (Outcome = 'Done' or Outcome = 'Error' or Outcome = 'Queued')
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)
        return todo

    def get_masks_to_qc(self, project):
        sql = r"""
        SELECT DISTINCT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'Mask'
            AND Outcome = 'Done'
            AND ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE Project = {project}
                    AND Process = {process}
                    AND Step = 'MaskQC'
                    AND (Outcome = 'Pass' OR Outcome = 'Edit' OR Outcome = 'Fail')
            )
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)
        return todo

    def get_segs_to_qc(self, project):
        sql = r"""
        SELECT
            ScanCode AS Code
        FROM 
            ProcessingLog
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'MaskQC'
            AND Outcome = 'Pass'
            AND ScanCode NOT IN(
                SELECT
                    ScanCode
                FROM
                    ProcessingLog
                WHERE Project = {project}
                AND Process = {process}
                AND Step = 'SegQC'
                AND (Outcome = 'Pass' OR Outcome = 'Fail')
            )
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

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
        DELETE FROM pijp_dti WHERE ProjectID = {project_id} AND Code = {code} 
        """.format(project_id=project_id['ProjectID'], code=fsp(code))

        self.connection.execute_non_query(sql)

    def get_project_id(self, project):
        sql = r"""
        SELECT ProjectID FROM Projects WHERE ProjectName = {}
        """.format(fsp(project))

        project_id = self.connection.fetchone(sql)
        return project_id

    def find_where_left_off(self, project, step):

        sql = r"""
        SELECT ScanCode as Code, Outcome, Comments
        FROM ProcessingLog
        WHERE Project = {project}
        AND Process = {process}
        AND Step = {step} 
        AND CompletedBy = {user} 
        ORDER BY CompletedOn DESC
        """.format(project=fsp(project), step=fsp(step),
                   process=fsp(PROCESS_TITLE), user=fsp(getpass.getuser()))

        left_off = self.connection.fetchone(sql)
        return left_off

    def get_t2(self, project, code):
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
            AND ScanCode LIKE '%{code}%'
            AND SeriesDescription LIKE '%PD%'
        """.format(project=fsp(project), code=code)

        todo = self.connection.fetchone(sql)
        if todo is not None:
            todo = todo["Code"]
        return todo

    def get_nnicv(self, project, code):
        code = '-'.join(code.split('-')[0:-1])
        sql = r"""
        SELECT
            ScanCode AS Code
        FROM ProcessingLog
        WHERE
            Project = {project}
            AND Process = 'NNICV'
            AND ScanCode LIKE '%{code}%'
        """.format(project=fsp(project), code=code)

        todo = self.connection.fetchone(sql)
        project_dir = get_project_dir(project)
        if todo is not None:
            full_code = todo["Code"]
            nnicv_path = f"NeuralNetICV/{full_code}/ICV/" \
                         f"{full_code}_ICV_T2_Automated-Mask.nii.gz"
            full_path = os.path.join(project_dir, nnicv_path)
        else:
            full_path = None

        return full_path

    def get_T2(self, project, code):
        code = '-'.join(code.split('-')[0:-1])
        sql = r"""
        SELECT
            ScanCode AS Code
        FROM ProcessingLog
        WHERE
            Project = {project}
            AND Process = 'NNICV'
            AND ScanCode LIKE '%{code}%'
        """.format(project=fsp(project), code=code)

        todo = self.connection.fetchone(sql)
        project_dir = get_project_dir(project)
        if todo is not None:
            full_code = todo["Code"]
            nnicv_path = f"NeuralNetICV/{full_code}/stage/" \
                         f"unregisteredT2_e2.nii.gz"
            full_path = os.path.join(project_dir, nnicv_path)
        else:
            full_path = None

        return full_path
