    """getting args from command line"""

    def isValidTime(validtime: str):
        """check the time format and return the time if it is valid, otherwise return parser error"""
        try:
            t = datetime.strptime(validtime, "%H:%M").strftime("%H:%M")
        except ValueError:
            parser.error("Invalid time format, use HH:MM")
        else:
            return t

    def isSessionExist(session: str):
        """check if the session is valid and return the session if it is valid, otherwise return parser error"""
        if Path(f"{Path(__file__).parent}/Profiles/{session}").exists():
            return session
        else:
            parser.error(f"Session not found for {session}")

    parser = ArgumentParser(
        description="Microsoft Rewards Farmer V2.1",
        allow_abbrev=False,
        usage="You may use execute the program with the default config or use arguments to configure available options."
    )
    parser.add_argument('--everyday',
                        action='store_true',
                        help='This argument will make the script run everyday at the time you start.',
                        required=False)
    parser.add_argument('--headless',
                        help='Enable headless browser.',
                        action='store_true',
                        required=False)
    parser.add_argument('--session',
                        help='Creates session for each account and use it.',
                        action='store_true',
                        required=False)
    parser.add_argument('--error',
                        help='Display errors when app fails.',
                        action='store_true',
                        required=False)
    parser.add_argument('--fast',
                        help="Reduce delays where ever it's possible to make script faster.",
                        action='store_true',
                        required=False)
    parser.add_argument('--superfast',
                        help="Reduce delays SUPER FAST where ever it's possible to make script faster.",
                        action='store_true',
                        required=False)
    parser.add_argument('--telegram',
                        metavar=('<API_TOKEN>', '<CHAT_ID>'),
                        nargs=2,
                        help='This argument takes token and chat id to send logs to Telegram.',
                        type=str,
                        required=False)
    parser.add_argument('--discord',
                        metavar='<WEBHOOK_URL>',
                        nargs=1,
                        help='This argument takes webhook url to send logs to Discord.',
                        type=str,
                        required=False)
    parser.add_argument('--edge',
                        help='Use Microsoft Edge webdriver instead of Chrome.',
                        action='store_true',
                        required=False)
    parser.add_argument('--account-browser',
                        nargs=1,
                        type=isSessionExist,
                        help='Open browser session for chosen account.',
                        required=False)
    parser.add_argument('--start-at',
                        metavar='<HH:MM>',
                        help='Start the script at the specified time in 24h format (HH:MM).',
                        nargs=1,
                        type=isValidTime)
    parser.add_argument("--on-finish",
                        help="Action to perform on finish from one of the following: shutdown, sleep, hibernate, exit",
                        choices=["shutdown", "sleep", "hibernate", "exit"],
                        required=False,
                        metavar="ACTION")
    parser.add_argument("--redeem",
                        help="[Optional] Enable auto-redeem rewards based on accounts.json goals.",
                        action="store_true",
                        required=False)
    parser.add_argument("--calculator",
                        help="MS Rewards Calculator",
                        action='store_true',
                        required=False)
    parser.add_argument("--skip-unusual",
                        help="Skip unusual activity detection.",
                        action="store_true",
                        required=False)
    parser.add_argument("--skip-shopping",
                        help="Skip MSN shopping game (useful for people living in regions which do not support MSN Shopping.",
                        action="store_true",
                        required=False)

    args = parser.parse_args()
    if args.superfast or args.fast:
        global SUPER_FAST, FAST  # pylint: disable=global-statement
        SUPER_FAST = args.superfast
        if args.fast and not args.superfast:
            FAST = True
    if len(sys.argv) > 1 and not args.calculator:
        for arg in vars(args):
            prBlue(f"[INFO] {arg}: {getattr(args, arg)}")
    return args
