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
    query GetAPITokens {
        apitokens(where: {active: {_eq: true}}) {
            token_value
            active
            id
        }
    }
    """
)
create_task = gql(
    """
    mutation createTasking($callback_id: Int!, $command: String!, $params: String!, $token_id: Int, $tasking_location: String, $original_params: String, $parameter_group_name: String) {
        createTask(callback_id: $callback_id, command: $command, params: $params, token: $token_id, tasking_location: $tasking_location, original_params: $original_params, parameter_group_name: $parameter_group_name) {
            status
            id
            error
        }
    }
"""
)
update_callback_active_status = gql(
    """
    mutation updateActiveCallback ($callback_id: Int!, $active: Boolean!){
        updateCallback(input: {callback_id: $callback_id, active: $active}) {
            status
            error
        }
    }
    """
)
update_callback_lock_status = gql(
    """
    mutation lockCallack($callback_id: Int!, $locked: Boolean!){
        updateCallback(input: {callback_id: $callback_id, locked: $locked}) {
            status
            error
        }
    }
    """
)
update_callback_description = gql(
    """
    mutation updateDescriptionCallack($callback_id: Int!, $description: String!){
        updateCallback(input: {callback_id: $callback_id, description: $description}) {
            status
            error
        }
    }
    """
)
update_callback_sleep_info = gql(
    """
    mutation updateSleepInfoCallback($callback_id: Int!, $sleep_info: String!){
        update_callback_by_pk(pk_columns: {id: $callback_id}, _set: {sleep_info: $sleep_info}){
            id
            sleep_info
        }
    }
    """
)
task_fragment = """
    fragment task_fragment on task {
        callback_id
        id
        operator{
            username
        }
        status
        original_params
        display_params
        timestamp
        command_name
        tasks {
            id
        }
        token {
            id
        }
    }
    """
filebrowser_fragment = """
    fragment filebrowser_fragment on filebrowserobj {
        comment
        full_path_text
        host
        id
        is_file
        modify_time
        name_text
        parent_path_text
        permissions
        timestamp
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
                ptype
            }
            tag
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
    fragment add_operator_to_operation_fragment on operatoroperation{
        id
        view_mode
    }
"""
remove_operator_from_operation_fragment = """
    fragment remove_operator_from_operation_fragment on operatoroperation{
        id
    }
"""
update_operator_in_operation_fragment = """
    fragment update_operator_in_operation_fragment on operatoroperation{
        id
        view_mode
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
            agent_task_id
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
  tag
  deleted
  auto_generated
  payloadtype {
    id
    ptype
  }
  filemetum {
    agent_file_id
    filename_text
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
process_data_fragment = """
fragment process_data_fragment on process {
    name
    process_id
    parent_process_id
    architecture
    bin_path
    integrity_level
    id
    user
}
"""
file_data_fragment = """
fragment file_data_fragment on filemeta{
    agent_file_id
    chunk_size
    chunks_received
    complete
    deleted
    filename_text
    full_remote_path_text
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
