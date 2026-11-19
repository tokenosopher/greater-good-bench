for f in ('build_scene.py', 'build_model.py', 'build_legend.py', 'build_stage.py'):
    exec(compile(open(f).read(), f, 'exec'), globals())
exec(compile(open('build_export.py').read(), 'build_export.py', 'exec'), globals())
