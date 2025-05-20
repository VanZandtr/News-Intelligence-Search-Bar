def open_link(event):
    """Open the clicked link in the default web browser"""
    import webbrowser
    # Find which link was clicked
    for start, end, url in event.widget.master.links:
        if event.widget.compare(start, "<=", f"@{event.x},{event.y}") and \
            event.widget.compare(end, ">=", f"@{event.x},{event.y}"):
            webbrowser.open(url)
            break