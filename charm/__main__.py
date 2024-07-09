from charm import main

# -- TEMP --
import arrow
import cProfile
import pstats

if __name__ == "__main__":
    launch_time = arrow.now()
    main.main()

    # with cProfile.Profile() as pr:
    #     main.main()

    # with open(f'./debug/launch_{launch_time.format("YYYY-MM-DD_HH-mm-ss")}.prof', 'w') as output:
    #     stats = pstats.Stats(pr, stream=output)
    #     stats.sort_stats('cumulative')
    #     stats.print_stats()
    # main.main()
