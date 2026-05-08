pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 45, unit: 'MINUTES')
    }

    parameters {
        string(
            name: 'APP_REPO',
            defaultValue: 'https://github.com/Imranay/IdeaThoughts.git',
            description: 'GitHub URL of the IdeaThoughts application repository'
        )

        string(
            name: 'TEST_REPO',
            defaultValue: 'https://github.com/Imranay/IdeaThoughts-Selenium-Tests.git',
            description: 'GitHub URL of the Selenium test repository'
        )

        string(
            name: 'APP_PORT',
            defaultValue: '9090',
            description: 'Public/local port where Flask app is exposed'
        )

        string(
            name: 'PUBLIC_APP_URL',
            defaultValue: '',
            description: 'Optional public application URL. Leave empty to auto-detect EC2 public IP.'
        )

        string(
            name: 'DEFAULT_RECIPIENTS',
            defaultValue: 'qasimalik@gmail.com',
            description: 'Default email recipients. Comma-separated emails allowed.'
        )
    }

    environment {
        LOCAL_APP_URL = "http://127.0.0.1:${params.APP_PORT}"
        TEST_IMAGE = "ideathoughts-selenium-tests:${BUILD_NUMBER}"
        EMAIL_RECIPIENTS = ""
        PUBLIC_APP_URL_FINAL = ""
        COMMIT_AUTHOR_EMAIL = ""
        COMMIT_AUTHOR_NAME = ""
    }

    stages {

        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Clone Selenium Test Code') {
            steps {
                sh 'git clone ${TEST_REPO} tests'

                dir('tests') {
                    script {
                        env.COMMIT_AUTHOR_EMAIL = sh(
                            script: "git log -1 --pretty=%ae || true",
                            returnStdout: true
                        ).trim()

                        env.COMMIT_AUTHOR_NAME = sh(
                            script: "git log -1 --pretty=%an || true",
                            returnStdout: true
                        ).trim()

                        echo "Latest Commit Author: ${env.COMMIT_AUTHOR_NAME}"
                        echo "Latest Commit Author Email: ${env.COMMIT_AUTHOR_EMAIL}"
                    }
                }
            }
        }

        stage('Prepare Dynamic Values') {
            steps {
                script {
                    // Build dynamic public application URL
                    if (params.PUBLIC_APP_URL?.trim()) {
                        env.PUBLIC_APP_URL_FINAL = params.PUBLIC_APP_URL.trim()
                    } else {
                        def detectedIp = sh(
                            script: '''
                            TOKEN=$(curl -sS --max-time 2 -X PUT "http://169.254.169.254/latest/api/token" \
                              -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" || true)

                            if [ -n "$TOKEN" ]; then
                              IP=$(curl -sS --max-time 2 \
                                -H "X-aws-ec2-metadata-token: $TOKEN" \
                                http://169.254.169.254/latest/meta-data/public-ipv4 || true)
                            fi

                            if [ -z "$IP" ]; then
                              IP=$(hostname -I | awk '{print $1}')
                            fi

                            echo "$IP"
                            ''',
                            returnStdout: true
                        ).trim()

                        env.PUBLIC_APP_URL_FINAL = "http://${detectedIp}:${params.APP_PORT}"
                    }

                    // Build dynamic email recipient list
                    def recipients = []

                    if (params.DEFAULT_RECIPIENTS?.trim()) {
                        recipients.addAll(
                            params.DEFAULT_RECIPIENTS
                                .split(',')
                                .collect { it.trim() }
                                .findAll { it }
                        )
                    }

                    if (env.COMMIT_AUTHOR_EMAIL ==~ /(?i)^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/) {
                        recipients.add(env.COMMIT_AUTHOR_EMAIL)
                    }

                    env.EMAIL_RECIPIENTS = recipients.unique().join(',')

                    echo "Local App URL: ${env.LOCAL_APP_URL}"
                    echo "Public App URL: ${env.PUBLIC_APP_URL_FINAL}"
                    echo "Email Recipients: ${env.EMAIL_RECIPIENTS}"
                }
            }
        }

        stage('Clone IdeaThoughts Application') {
            steps {
                sh 'git clone ${APP_REPO} app'
            }
        }

        stage('Start IdeaThoughts Application') {
            steps {
                dir('app') {
                    sh '''
                    echo "Cleaning old IdeaThoughts containers if they exist..."

                    docker rm -f ideathoughts_app ideathoughts_db || true
                    docker compose down -v --remove-orphans || true

                    echo "Starting IdeaThoughts application using Docker Compose..."

                    docker compose up -d --build

                    echo "Waiting for database and Flask app to become ready..."
                    sleep 60

                    docker ps
                    '''
                }
            }
        }

        stage('Check Application Reachability') {
            steps {
                sh '''
                echo "Checking application at: $LOCAL_APP_URL"

                for i in $(seq 1 30); do
                    if curl -fsS "$LOCAL_APP_URL" > /dev/null; then
                        echo "Application is reachable."
                        exit 0
                    fi

                    echo "Application not ready yet. Attempt $i/30"
                    sleep 5
                done

                echo "Application failed to become reachable."
                echo "App container logs:"
                docker logs ideathoughts_app || true

                echo "Database container logs:"
                docker logs ideathoughts_db || true

                exit 1
                '''
            }
        }

        stage('Build Selenium Test Image') {
            steps {
                dir('tests') {
                    sh '''
                    echo "Building Selenium test Docker image..."
                    docker build -t $TEST_IMAGE .
                    '''
                }
            }
        }

        stage('Run Selenium Tests in Docker') {
            steps {
                dir('tests') {
                    sh '''
                    mkdir -p reports

                    echo "Running Selenium tests against: $LOCAL_APP_URL"

                    docker run --rm \
                      --network host \
                      -e APP_URL=$LOCAL_APP_URL \
                      -v "$PWD/reports:/tests/reports" \
                      $TEST_IMAGE
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Archiving Selenium test reports..."

            archiveArtifacts artifacts: 'tests/reports/*', allowEmptyArchive: true
            junit testResults: 'tests/reports/results.xml', allowEmptyResults: true

            echo "Sending pipeline email notification..."

            mail(
                to: "${env.EMAIL_RECIPIENTS}",
                subject: "IdeaThoughts Jenkins Test Result: ${currentBuild.currentResult} | Build #${env.BUILD_NUMBER}",
                body: """
Project: IdeaThoughts

Build Status:
${currentBuild.currentResult}

Build Number:
${env.BUILD_NUMBER}

Triggered Commit Author:
${env.COMMIT_AUTHOR_NAME}

Commit Author Email:
${env.COMMIT_AUTHOR_EMAIL}

Public Application URL:
${env.PUBLIC_APP_URL_FINAL}

Local Application URL Used for Selenium:
${env.LOCAL_APP_URL}

Jenkins Build URL:
${env.BUILD_URL}

Selenium test results are available inside Jenkins build artifacts.
"""
            )
        }

        cleanup {
            echo "Cleaning Docker containers after pipeline..."

            dir('app') {
                sh '''
                docker compose down -v --remove-orphans || true
                docker rm -f ideathoughts_app ideathoughts_db || true
                '''
            }

            sh '''
            docker rmi $TEST_IMAGE || true
            docker system prune -f || true
            '''
        }
    }
}