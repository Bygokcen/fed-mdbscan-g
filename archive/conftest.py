# The frozen snapshots carry their own copies of the test suite; collecting them
# next to new_work/tests clashes on module names. They are records, not tests.
collect_ignore_glob = ["frozen_sources/*"]
