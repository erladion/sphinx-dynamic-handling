import os

def setup(app):
    """
    This function registers a 'env' variable containing all environment
    variables, making them accessible via app.config.env in ifconfig.
    """
    # The 'env' dictionary is a copy of os.environ, converted to a standard dict
    # and registered as a custom config value.
    app.add_config_value(
        'env', 
        dict(os.environ), 
        'env'  # 'env' rebuild type ensures a full rebuild if environment changes
    )
    
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }