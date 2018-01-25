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
				}
				
            }

        }

        stage('Тестирование кода пакета LINUX') {

            agent { label 'master' }

            steps {
                echo 'under development'
            }

        }

        stage('Сборка пакета') {

            agent { label 'windows' }

            steps {
                checkout scm

                bat 'erase /Q *.ospx'
                bat 'chcp 65001 > nul && call opm build .'

                stash includes: '*.ospx', name: 'package'
				archiveArtifacts '*.ospx'
            }

        }
		
		stage('Публикация в хабе') {
			when {
                branch 'master'
            }
			agent { label 'master' }
			steps {
				sh 'rm -f *.ospx'
				unstash 'package'

				sh '''
                artifact=`ls -1 *.ospx`
                basename=`echo $artifact | sed -r 's/(.+)-.*(.ospx)/\\1/'`
                cp $artifact $basename.ospx
                sudo rsync -rv *.ospx /var/www/hub.oscript.io/download/$basename/
                '''.stripIndent()
			}
		}

        stage('Публикация в нестабильном хабе') {
			when {
                branch 'develop'
            }
			agent { label 'master' }
			steps {
				sh 'rm -f *.ospx'
				unstash 'package'

				sh '''
                artifact=`ls -1 *.ospx`
                basename=`echo $artifact | sed -r 's/(.+)-.*(.ospx)/\\1/'`
                cp $artifact $basename.ospx
                sudo rsync -rv *.ospx /var/www/hub.oscript.io/dev-channel/$basename/
                '''.stripIndent()
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
