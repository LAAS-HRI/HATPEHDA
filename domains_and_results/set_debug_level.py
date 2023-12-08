import sys

file = open("log.conf", "w")

debug_levels = {"1":"DEBUG", "2":"INFO", "3":"WARNING", "4":"ERROR", "5":"CRITICAL"}
format = "%(message)s"
# format = "%(asctime)s - %(levelname)s - %(message)s"

if len(sys.argv)==2 and sys.argv[1] in debug_levels:
    debug_level = debug_levels[sys.argv[1]]
else:
    while True:
        print("Possible debug level:")
        for k in debug_levels:
            print(f"\t{k} - {debug_levels[k]}")
        print("Select a level: ", end="")

        debug_level = input()
        if debug_level in debug_levels:
            debug_level = debug_levels[debug_level]
            break

print(f"Debug level set to : {debug_level}")

content_log_file = f"[loggers]\nkeys=root\n\n[handlers]\nkeys=consoleHandler\n\n[formatters]\nkeys=simpleFormatter\n\n[logger_root]\nlevel={debug_level}\nhandlers=consoleHandler\n\n[handler_consoleHandler]\nclass=StreamHandler\nformatter=simpleFormatter\nargs=(sys.stdout,)\n\n[formatter_simpleFormatter]\nformat={format}\n"

file.write(content_log_file)
file.close()


