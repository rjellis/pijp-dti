from pijp.repositories import BaseRepository
from pijp import dbprocs


class DTIRepository(BaseRepository):
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
        WHERE 
            st.StudyCode = {project} 
        AND 
            SeriesDescription LIKE '%MR 2D AXIAL DTI BRAIN%'
        """.format(project=dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo
