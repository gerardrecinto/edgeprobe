pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'PYTHONPATH=src python3 -m unittest discover -s tests'
            }
        }
        stage('Build Image') {
            steps {
                sh 'docker build -t edgeprobe:${BUILD_NUMBER} .'
            }
        }
        stage('Analyze Golden Snapshot') {
            steps {
                sh 'PYTHONPATH=src python3 -m edgeprobe analyze tests/fixtures/host-snapshot --output json > edgeprobe-report.json || test $? -eq 2'
                archiveArtifacts artifacts: 'edgeprobe-report.json', fingerprint: true
            }
        }
    }
}

