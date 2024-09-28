{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "core-keeper-dedicated-server.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "core-keeper-dedicated-server.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "core-keeper-dedicated-server.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "core-keeper-dedicated-server.labels" -}}
app.kubernetes.io/name: {{ include "core-keeper-dedicated-server.name" . }}
helm.sh/chart: {{ include "core-keeper-dedicated-server.chart" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "core-keeper-dedicated-server.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "core-keeper-dedicated-server.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}


{{/*
Convert difficulty string into the value
*/}}
{{- define "core-keeper-dedicated-server.difficulty" -}}
{{- if eq .Values.corekeeper.config.difficulty "normal" -}}
    "0"
{{- else if eq .Values.corekeeper.config.difficulty "hard" -}}
    "1"
{{- else if eq .Values.corekeeper.config.difficulty "creative" -}}
    "2"
{{- else if eq .Values.corekeeper.config.difficulty "casual" -}}
    "3"
{{- else -}}
    "0" {{/* default to normal */}}
{{- end -}}
{{- end -}}


{{- if not (or (eq (len .Values.corekeeper.config.gameID) 0) (eq (len .Values.corekeeper.config.gameID) 28)) }}
{{- fail "the GameID must be either 0 or exactly 28 characters long." }}
{{- end }}
