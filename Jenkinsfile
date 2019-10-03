pipeline {
    agent none
    options {
        buildDiscarder(logRotator(numToKeepStr: '7'))
        skipDefaultCheckout()
    }
    
    stages {
        stage('Тестирование кода пакета WIN') {

            agent { label 'windows' }

            steps {
                checkout scm
				
                script {
					bat 'chcp 65001 > nul && opm install -l'

					if( fileExists ('tasks/test.os') ){
                        try {
                            cmd("oscript tasks/test.os")
                            junit 'tests.xml'
                        } catch (Exception err) {
                            junit 'tests.xml'
                            //throw err;
                        }
					}
					else
						echo 'no testing task'

                    def scannerHome = tool 'sonar-scanner';
                    withSonarQubeEnv('silverbulleters') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
				}
				
            }

        }

        stage('Тестирование кода пакета LINUX') {

            agent { label 'master' }

            steps {
                echo 'under development'
            }

        }

    }
}

def cmd(command) {
    if (isUnix()) {
        sh "${command}"
    } else {
         bat "chcp 65001\n${command}"
    }
}
