from pipelines.gitpipeline import GitPipelines

def main():
    execute = GitPipelines()
    #execute.main()

    print(execute.call_procedure())

if __name__ == '__main__':
    main()