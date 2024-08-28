from gql import gql

create_apitoken = gql(
    """
    mutation createAPITokenMutation{
        createAPIToken(token_type: "User"){
            id
            token_value
            status
            error
            operator_id
        }
    }
    """
)
get_apitokens = gql(
    """
    query GetAPITokens($username: String!) {
        apitokens(where: {active: {_eq: true}, operator: {username: {_eq: $username}}, deleted: {_eq: false}}) {
            token_value
            active
            id
        }
    }
    """
)
create_task = gql(
    """
    mutation createTasking($callback_id: Int!, $command: String!, $params: String!, $files: [String], $token_id: Int, $tasking_location: String, $original_params: String, $parameter_group_name: String, $is_interactive_task: Boolean, $interactive_task_type: Int, $parent_task_id: Int) {
        createTask(callback_id: $callback_id, command: $command, params: $params, files: $files, token_id: $token_id, tasking_location: $tasking_location, original_params: $original_params, parameter_group_name: $parameter_group_name, is_interactive_task: $is_interactive_task, interactive_task_type: $interactive_task_type, parent_task_id: $parent_task_id) {
            status
            id
            display_id
            error
        }
    }
"""
)
update_callback = gql(
    """
    mutation updateCallbackInformation ($callback_display_id: Int!, $active: Boolean, $locked: Boolean, $description: String, $ips: [String], $user: String, $host: String, $os: String, $architecture: String, $extra_info: String, $sleep_info: String, $pid: Int, $process_name: String, $integrity_level: Int, $domain: String){
        updateCallback(input: {callback_display_id: $callback_display_id, active: $active, locked: $locked, description: $description, ips: $ips, user: $user, host: $host, os: $os, architecture: $architecture, extra_info: $extra_info, sleep_info: $sleep_info, pid: $pid, process_name: $process_name, integrity_level: $integrity_level, domain: $domain}) {
            status
            error
        }
    }
    """
)

task_fragment = """
    fragment task_fragment on task {
        callback {
            id
            display_id
        }
        id
        display_id
        operator{
            username
        }
        status
        completed
        original_params
        display_params
        timestamp
        command_name
        tasks {
            id
        }
        token {
            token_id
        }
    }
    """
mythictree_fragment = """
    fragment mythictree_fragment on mythictree {
        task_id
        timestamp
        host
        comment
        success
        deleted
        tree_type
        os
        can_have_children
        name_text
        parent_path_text
        full_path_text
        metadata
    }
"""
operator_fragment = """
    fragment operator_fragment on operator {
        id
        username
        admin
        active
        last_login
        current_operation_id
        deleted
    }
"""
callback_fragment = """
    fragment callback_fragment on callback {
        architecture
        description
        domain
        external_ip
        host
        id
        display_id
        integrity_level
        ip
        extra_info
        sleep_info
        pid
        os
        user
        agent_callback_id
        operation_id
        process_name
        payload {
            os
            payloadtype {
                name
            }
            description
            uuid
        }
    }
"""
payload_build_fragment = """
    fragment payload_build_fragment on payload {
        build_phase
        uuid
        build_stdout
        build_stderr
        build_message
        id
    }
"""
create_payload = gql(
    """
    mutation createPayloadMutation($payload: String!) {
        createPayload(payloadDefinition: $payload) {
            error
            status
            uuid
        }
    }
    """
)
create_operator_fragment = """
    fragment create_operator_fragment on OperatorOutput {
        active
        creation_time
        deleted
        error
        id
        last_login
        status
        username
        view_utc_time
    }
"""
create_operator = gql(
    f"""
    mutation NewOperator($username: String!, $password: String!) {{
        createOperator(input: {{password: $password, username: $username}}) {{
            ...create_operator_fragment
        }}
    }}
    {create_operator_fragment}
    """
)
get_operations_fragment = """
    fragment get_operations_fragment on operation {
        complete
        name
        id
        admin {
            username
            id
        }
        operatoroperations {
            view_mode
            operator {
                username
                id
            }
            id
        }
    }
"""
get_operation_and_operator_by_name = gql(
    """
    query getOperationAndOperator($operation_name: String!, $operator_username: String!){
        operation(where: {name: {_eq: $operation_name}}){
            id
            operatoroperations(where: {operator: {username: {_eq: $operator_username}}}) {
                view_mode
                id
            }
        }
        operator(where: {username: {_eq: $operator_username}}){
            id
        }
    }
    """
)
add_operator_to_operation_fragment = """
    fragment add_operator_to_operation_fragment on updateOperatorOperation{
        status
        error
    }
"""
remove_operator_from_operation_fragment = """
    fragment remove_operator_from_operation_fragment on updateOperatorOperation{
        status
        error
    }
"""
update_operator_in_operation_fragment = """
    fragment update_operator_in_operation_fragment on updateOperatorOperation{
        status
        error
    }
"""
create_operation_fragment = """
    fragment create_operation_fragment on createOperationOutput {
        status
        error
        operation{
            name
            id
            admin {
                id
                username
            }
        }
    }
"""
user_output_fragment = """
    fragment user_output_fragment on response {
        response_text
        timestamp
    }
"""
task_output_fragment = """
    fragment task_output_fragment on response {
        id
        timestamp
        response_text
        task {
            id
            display_id
            status
            completed
            agent_task_id
            command_name
        }
    }
"""
payload_data_fragment = """
fragment payload_data_fragment on payload {
  build_message
  build_phase
  build_stderr
  callback_alert
  creation_time
  id
  operator {
    id
    username
  }
  uuid
  description
  deleted
  auto_generated
  payloadtype {
    id
    name
  }
  filemetum {
    agent_file_id
    filename_utf8
    id
  }
  payloadc2profiles {
    c2profile {
      running
      name
      is_p2p
      container_running
    }
  }
}
"""
file_data_fragment = """
fragment file_data_fragment on filemeta{
    agent_file_id
    chunk_size
    chunks_received
    complete
    deleted
    filename_utf8
    full_remote_path_utf8
    host
    id
    is_download_from_agent
    is_payload
    is_screenshot
    md5
    operator {
        id
        username
    }
    comment
    sha1
    timestamp
    total_chunks
    task {
        id
        comment
        command {
            cmd
            id
        }
    }
}
"""
command_fragment = """
fragment command_fragment on command {
    id
    cmd
    attributes
}
"""
