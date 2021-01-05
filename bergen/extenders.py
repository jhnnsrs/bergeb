

class UserPrettifier(object):
    ''' Just a little helper to make our User look nicer in Jupyter Notebooks'''

    def _repr_html_(self):
        string = f"{self.username}</br>"
        if self.avatar is not None:
            string += f"<img src='{self.avatar.avatar}' alt='userimage'></img>"
        
        return string