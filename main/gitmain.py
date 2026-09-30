from pipelines.gitpipeline import GitPipelines

def main():
    execute = GitPipelines()
    #execute.main()

    print(execute.send_report_to_lark())

if __name__ == '__main__':
    main()