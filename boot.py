from applications import ProcessAllocation

if __name__ == '__main__':
    booter = ProcessAllocation()

    print('Loading Application Boot Manager ... \n')
    booter.fetch_tokens()
    booter.initialize()
