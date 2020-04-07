import re

from flask import request, Blueprint, jsonify, g
from flask_request_validator import (
    GET,
    PATH,
    JSON,
    Param,
    Pattern,
    MinLength,
    MaxLength,
    validate_params
)

from seller.service.seller_service import SellerService
from connection import get_db_connection
from utils import login_required


class SellerView:
    """ 셀러 뷰

    Authors:
        leesh3@brandi.co.kr (이소헌)
    History:
        2020-03-25 (leesh3@brandi.co.kr): 초기 생성

    """
    seller_app = Blueprint('seller_app', __name__, url_prefix='/seller')

    @seller_app.route('/<int:parameter_account_no>/password', methods=['PUT'], endpoint='change_password')
    @login_required
    @validate_params(
        Param('parameter_account_no', PATH, int),
        Param('original_password', JSON, str, required=False),
        Param('new_password', JSON, str),
    )
    def change_password(*args):
        """ 계정 비밀번호 변경 엔드포인트

        계정 비밀번호 변경 엔드포인트 입니다.
        계정이 가진 권한에 따라 지정된 인자를 받아 비밀번호를 변경합니다.
        url 에 비밀번호를 바꿔야할 계정 번호를 받습니다.

        Args:
            *args: 유효성 검사를 통과한 파라미터

        url parameter:
            parameter_account_no: 비밀번호가 바뀌어야할 계정 번호

        g.account_info: 데코레이터에서 넘겨받은 계정 정보
            auth_type_id: 계정의 권한정보
            account_no: 데코레이터에서 확인된 계정번호

        request.body: request로 전달 받은 정보
            original_password: 기존 비밀번호(마스터는 안보내줌)
            new_password: 새로운 비밀번호

        Returns: http 응답코드
            200: SUCCESS 비밀번호 변경 완료
            400: VALIDATION_ERROR, INVALID_AUTH_TYPE_ID, NO_ORIGINAL_PASSWORD
            401: INVALID_PASSWORD
            500: DB_CURSOR_ERROR, SERVER_ERROR, NO_DATABASE_CONNECTION

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-03-31 (leejm3@brandi.co.kr): 초기 생성
            2020-04-02 (leejm3@brandi.co.kr): 파라미터 validation 추가, 데코레이터 적용
            2020-04-06 (leejm3@brandi.co.kr):
                url path 변경('/<int:parameter_account_no>' -> '/<int:parameter_account_no>/password')

        """

        # validation 확인이 된 data 를 account_info 로 재정의
        account_info = {
            'parameter_account_no': args[0],
            'original_password': args[1],
            'new_password': args[2],
            'auth_type_id': g.account_info['auth_type_id'],
            'account_no': g.account_info['account_no'],

        }

        # 셀러 권한일 때 original_password 가 없으면 에러반환
        if account_info['auth_type_id'] == 2:
            if account_info['original_password'] is None:
                return jsonify({"message": "NO_ORIGINAL_PASSWORD"}), 400

        db_connection = get_db_connection()
        if db_connection:
            try:
                seller_service = SellerService()
                changing_password_result = seller_service.change_password(account_info, db_connection)
                return changing_password_result

            except Exception as e:
                return jsonify({'message': f'{e}'}), 400

            finally:
                try:
                    db_connection.close()
                except Exception as e:
                    return jsonify({'message': f'{e}'}), 400

        else:
            return jsonify({'message': 'NO_DATABASE_CONNECTION'}), 500

    @seller_app.route('/<int:parameter_account_no>', methods=['GET'], endpoint='get_seller_info')
    @login_required
    @validate_params(
        Param('parameter_account_no', PATH, int),
        Param('parameter_account_no', PATH, str, rules=[MaxLength(6)]),
    )
    def get_seller_info(*args):

        """ 계정 셀러정보 표출 엔드포인트

        셀러정보를 표출하는 엔드포인트 입니다.
        url 로 셀러정보를 확인하고 싶은 계정 번호를 받습니다.

        셀러정보를 열람을 수행하려는 계정의 번호를 데코레이터로부터 받습니다.
        열람 대상 셀러정보의 계정의 번호를 url parameter 로 받습니다.

        받은 정보를 유효성 검사를 거친 후 account_info 로 저장해 service 로 넘겨줍니다.

        Args:
            *args: 유효성 검사를 통과한 파라미터

        url parameter:
            parameter_account_no: 열람하고자 하는 셀러정보의 계정 번호

        g.account_info: 데코레이터에서 넘겨받은(셀러정보를 열람을 수행하려는) 계정 정보
            auth_type_id: 계정의 권한정보
            account_no: 데코레이터에서 확인된 계정번호

        Returns: http 응답코드
            200: SUCCESS 비밀번호 변경 완료
            400: INVALID_KEY
            400: VALIDATION_ERROR, INVALID_AUTH_TYPE_ID
            401: INVALID_PASSWORD
            500: SERVER ERROR, DB_CURSOR_ERROR, NO_DATABASE_CONNECTION

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-01 (leejm3@brandi.co.kr): 초기 생성
            2020-04-02 (leejm3@brandi.co.kr): 파라미터 validation 추가, 데코레이터 적용
            2020-04-03 (leejm3@brandil.co.kr): 주석 수정(메인문구, urlparameter 수정)
            2020-04-06 (leejm3@brandi.co.kr):
                url path 변경('/<int:parameter_account_no>/info' -> '/<int:parameter_account_no>')

        """

        # validation 확인이 된 data 를 account_info 로 재정의
        account_info = {
            'parameter_account_no': args[0],
            'auth_type_id': g.account_info['auth_type_id'],
            'decorator_account_no': g.account_info['account_no'],
        }

        db_connection = get_db_connection()
        if db_connection:
            try:
                seller_service = SellerService()

                getting_seller_info_result = seller_service.get_seller_info(account_info, db_connection)

                # 셀러정보가 존재하면 리턴
                if getting_seller_info_result:
                    return getting_seller_info_result

                # 셀러정보가 None 으로 들어오면 INVALID_ACCOUNT_NO 리턴
                else:
                    return jsonify({'message': 'INVALID_ACCOUNT_NO'}), 400

            except Exception as e:
                return jsonify({'message': f'{e}'}), 400

            finally:
                try:
                    db_connection.close()
                except Exception as e:
                    return jsonify({'message': f'{e}'}), 400

        else:
            return jsonify({'message': 'NO_DATABASE_CONNECTION'}), 500

    @seller_app.route('/list', methods=['GET'], endpoint='get_all_sellers')
    @login_required
    # @validate_params(
    #     Param('seller_account_no', PATH, int),
    #     Param('login_id', PATH, int),
    #     Param('name_en', PATH, str),
    #     Param('name_kr', PATH, str),
    #     Param('brandi_app_user_id', PATH, int),
    #     Param('manager_name', PATH, str),
    #     Param('seller_status', PATH, str),
    #     Param('manager_contact_number', PATH, str),
    #     Param('seller_type_name', PATH, str),
    #     Param('start_time', PATH, str),
    #     Param('close_time', PATH, str)
    #
    # )
    def get_seller_list():

        """ 가입된 모든 셀러 정보 리스트를 표출

        Returns:
            200: 가입된 모든 셀러 및 셀러 세부 정보 리스트로 표출

        Authors:
            yoonhc@barndi.co.kr (윤희철)

        History:
            2020-04-03 (yoonhc@brandi.co.kr): 초기 생성
        """
        db_connection = get_db_connection()

        # 유저 정보를 g에서 읽어와서 service에 전달
        user = g.account_info
        seller_service = SellerService()
        seller_list_result = seller_service.get_seller_list(request, user, db_connection)
        return seller_list_result

    @seller_app.route('/<int:parameter_account_no>', methods=['PUT'], endpoint='change_seller_info')
    @login_required
    @validate_params(
        Param('parameter_account_no', PATH, int),
        Param('profile_image_url', JSON, str,
              rules=[Pattern(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")]),
        Param('profile_image_url', JSON, str,
              rules=[MaxLength(200)]),
        Param('seller_status_no', JSON, int),
        Param('seller_type_no', JSON, int),
        Param('name_kr', JSON, str,
              rules=[Pattern(r'^[가-힣a-zA-Z0-9\ ]{1,45}$')]),
        Param('name_en', JSON, str,
              rules=[Pattern(r'^[a-z\ ]{1,45}$')]),
        Param('account_no', JSON, int),
        Param('brandi_app_user_app_id', JSON, str,
              rules=[Pattern(r'^[가-힣a-zA-Z0-9]{1,45}$')]),
        Param('ceo_name', JSON, str,
              rules=[Pattern(r'^[가-힣a-zA-Z0-9]{1,45}$')]),
        Param('company_name', JSON, str,
              rules=[Pattern(r'^[가-힣a-zA-Z0-9]{1,45}$')]),
        Param('business_number', JSON, str,
              rules=[Pattern(r'^[0-9]{3}-{1}[0-9]{2}-{1}[0-9]{5}$')]),
        Param('certificate_image_url', JSON, str,
              rules=[Pattern(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")]),
        Param('certificate_image_url', JSON, str,
              rules=[MaxLength(200)]),
        Param('online_business_number', JSON, str,
              rules=[MaxLength(45)]),
        Param('online_business_image_url', JSON, str,
              rules=[Pattern(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")]),
        Param('online_business_image_url', JSON, str,
              rules=[MaxLength(200)]),
        Param('background_image_url', JSON, str, required=False,
              rules=[Pattern(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")]),
        Param('background_image_url', JSON, str,
              rules=[MaxLength(200)]),
        Param('short_description', JSON, str,
              rules=[MaxLength(100)]),
        Param('long_description', JSON, str, required=False,
              rules=[MaxLength(200)]),
        Param('long_description', JSON, str, required=False,
              rules=[MinLength(10)]),
        Param('site_url', JSON, str,
              rules=[MaxLength(200)]),
        Param('site_url', JSON, str,
              rules=[Pattern(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")]),
        Param('manager_infos', JSON, list),
        Param('insta_id', JSON, str,
              rules=[Pattern(r"^[a-z0-9_\.]{1,45}$")]),
        Param('center_number', JSON, str,
              rules=[Pattern(r"^[0-9-]{1,14}$")]),
        Param('kakao_id', JSON, str, required=False,
              rules=[Pattern(r"^[가-힣a-zA-Z0-9_\.]{1,45}$")]),
        Param('yellow_id', JSON, str, required=False,
              rules=[Pattern(r"^[가-힣a-zA-Z0-9_\.]{1,45}$")]),
        Param('zip_code', JSON, str,
              rules=[Pattern(r"^[0-9]{5}$")]),
        Param('address', JSON, str,
              rules=[MaxLength(100)]),
        Param('detail_address', JSON, str,
              rules=[MaxLength(100)]),
        Param('weekday_start_time', JSON, str,
              rules=[Pattern(r"^[0-2]{2}:[0-5]{1}[0-9]{1}:[0-5]{1}[0-9]{1}$")]),
        Param('weekday_end_time', JSON, str,
              rules=[Pattern(r"^[0-2]{2}:[0-5]{1}[0-9]{1}:[0-5]{1}[0-9]{1}$")]),
        Param('weekend_start_time', JSON, str, required=False,
              rules=[Pattern(r"^[0-2]{2}:[0-5]{1}[0-9]{1}:[0-5]{1}[0-9]{1}$")]),
        Param('weekend_end_time', JSON, str, required=False,
              rules=[Pattern(r"^[0-2]{2}:[0-5]{1}[0-9]{1}:[0-5]{1}[0-9]{1}$")]),
        Param('bank_name', JSON, str,
              rules=[MaxLength(45)]),
        Param('bank_holder_name', JSON, str,
              rules=[MaxLength(45)]),
        Param('account_number', JSON, str,
              rules=[MaxLength(45)]),
        Param('seller_account_id', JSON, int),
        Param('previous_seller_info_no', JSON, int),
        Param('previous_seller_status_no', JSON, int),

        # int 를 str 로 인식해서 정규식 유효성 확인
        Param('seller_status_no', JSON, str,
              rules=[Pattern(r"^[1-5]{1}$")]),
        Param('seller_type_no', JSON, str,
              rules=[Pattern(r"^[1-7]{1}$")]),
        Param('previous_seller_status_no', JSON, str,
              rules=[Pattern(r"^[1-5]{1}$")])
    )
    def change_seller_info(*args):

        """ 계정 셀러정보 수정 엔드포인트

        셀러정보를 수정하는 엔드포인트 입니다.
        url 로 셀러정보를 수정하고 싶은 계정 번호를 받습니다.
        셀러정보 수정을 수행하려는 계정의 정보를 데코레이터로부터 받습니다.
        수정하려는 내용은 request.body 로 받습니다.

        받은 정보를 유효성 검사를 거친 후 account_info 로 저장해 service 로 넘겨줍니다.

        Args:
            *args: 유효성 검사를 통과한 파라미터

        url parameter:
            parameter_account_no: 저장할 셀러정보의 계정 번호

        g.account_info: 데코레이터에서 넘겨받은 수정을 수행하는 계정 정보
            auth_type_id: 계정의 권한정보
            account_no: 데코레이터에서 확인된 계정번호

        request.body:
            profile_image_url 프로필 이미지 URL str 200자
            seller_status_no 셀러 상태번호 int
            seller_type_no 셀러 속성번호 int
            name_kr 셀러 한글명 str 한글,영문,숫자
            name_en 셀러 영문명 str required False 영문 소문자
            account_no 계정번호 int
            seller_account_id 셀러 계정번호 int
            brandi_app_user_app_id 브랜디앱 유저 아이디 str
            ceo_name 대표자명 str
            company_name 사업자명 str
            business_number 사업자번호 str 12자리
            certificate_image_url 사업자등록증 이미지 URL
            online_business_number 통신판매업번호 str
            online_business_image_url 통신판매업신고필증 이미지 URL str
            background_image_url 셀러페이지 배경이미지 URL str required False
            short_description 셀러 한줄 소개 str
            long_description 셀러 상세 소개 str required False 10글자 이상
            site_url 사이트 URL str
            manager_info: 담당자 정보 list
            [
                {
                    name 담당자명 str
                    contact_number 담당자 핸드폰번호 str
                    email 담당자 이메일 str
                }
            ]
            insta_id 인스타그램 아이디 str
            center_number 고객센터 전화번호 str
            kakao_id 카카오톡 아이디 str required False
            yellow_id 옐로우 아이디 str required False
            zip_code 우편번호 str
            address 주소 int
            detail_address 상세주소 str
            weekday_start_time 고객센터 운영 시작시간(주중) str
            weekday_end_time 고객센터 운영 종료시간(주중) str
            weekend_start_time 고객센터 운영 시작시간(주말) str required False
            weekend_end_time 고객센터 운영 종료시간(주말) str required False
            bank_name 정산은행 str
            bank_holder_name 계좌주 str
            account_number 계좌번호 str
            previous_seller_info_no 이전 셀러 정보번호(수정하려고 하는) int
            previous_seller_status_no 이전 셀러정보의 상태번호 int (상태변경이력 체크용)

        Returns: http 응답코드
            200: SUCCESS 셀러정보 수정(새로운 이력 생성) 완료
            400: INVALID_APP_ID (존재하지 않는 브랜디 앱 아이디 입력)
            400: VALIDATION_ERROR_MANAGER_INFO, NO_SPECIFIC_MANAGER_INFO,
                 INVALID_AUTH_TYPE_ID
            403: NO_AUTHORIZATION
            500: SERVER_ERROR, DB_CURSOR_ERROR, NO_DATABASE_CONNECTION

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
            2020-04-03 (leejm3@brandi.co.kr): 초기 생성
            2020-04-04 (leejm3@brandi.co.kr): 이전 셀러 정보번호, 이전 셀러 정보 상태정보, 셀러 계정번호 추가
            2020-04-06 (leejm3@brandi.co.kr):
                url path 변경('/<int:parameter_account_no>/info' -> '/<int:parameter_account_no>')

        """

        # manager_infos 유효성 확인
        manager_info_list = args[24]

        # manger_infos 리스트를 돌면서 각각의 유효성을 충족하는지 체크
        for info in manager_info_list:
            name_validation = r'^[가-힣a-zA-Z0-9\ ]{1,45}$'
            contact_number_validation = r'^[0-9-]{1,14}$'
            email_validation = r'^[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}$'
            ranking_validation = r'^[1-3]{1}$'

            # 각 키가 들어왔는지 먼저 확인
            if (info.get('name', None) and
                    info.get('contact_number', None) and
                    info.get('email', None) and
                    info.get('ranking', None)):

                # 키가 모두 들어왔으면, 유효성을 만족하는지 확인
                if (re.match(name_validation, info['name']) and
                        re.match(contact_number_validation, info['contact_number']) and
                        re.match(email_validation, info['email']) and
                        re.match(ranking_validation, info['ranking'])):
                    pass

                # 유효성을 만족시키지 못하면 에러 반환
                else:
                    return jsonify({"message": "VALIDATION_ERROR_MANAGER_INFO"}), 400
            # 키가 안들어오면 에러 반환
            else:
                return jsonify({"message": "NO_SPECIFIC_MANAGER_INFO"}), 400

        # validation 확인이 된 data 를 account_info 로 재정의
        account_info = {
            'auth_type_id': g.account_info['auth_type_id'],
            'decorator_account_no': g.account_info['account_no'],
            'parameter_account_no': args[0],
            'profile_image_url': args[1],
            'seller_status_no': args[3],
            'seller_type_no': args[4],
            'name_kr': args[5],
            'name_en': args[6],
            'account_no': args[7],
            'brandi_app_user_app_id': args[8],
            'ceo_name': args[9],
            'company_name': args[10],
            'business_number': args[11],
            'certificate_image_url': args[12],
            'online_business_number': args[14],
            'online_business_image_url': args[15],
            'background_image_url': args[17],
            'short_description': args[19],
            'long_description': args[20],
            'site_url': args[22],
            'manager_infos': args[24],
            'insta_id': args[25],
            'center_number': args[26],
            'kakao_id': args[27],
            'yellow_id': args[28],
            'zip_code': args[29],
            'address': args[30],
            'detail_address': args[31],
            'weekday_start_time': args[32],
            'weekday_end_time': args[33],
            'weekend_start_time': args[34],
            'weekend_end_time': args[35],
            'bank_name': args[36],
            'bank_holder_name': args[37],
            'account_number': args[38],
            'seller_account_id': args[39],
            'previous_seller_info_no': args[40],
            'previous_seller_status_no': args[41]
        }

        # 데이터베이스 연결
        db_connection = get_db_connection()
        if db_connection:
            try:
                seller_service = SellerService()

                changing_seller_info_result = seller_service.change_seller_info(account_info, db_connection)
                return changing_seller_info_result

            except Exception as e:
                return jsonify({'message': f'{e}'}), 400

            finally:
                try:
                    db_connection.close()
                except Exception as e:
                    return jsonify({'message': f'{e}'}), 400
        else:
            return jsonify({'message': 'NO_DATABASE_CONNECTION'}), 500

    @seller_app.route('/name', methods=['GET'], endpoint='get_seller_name_list')
    @login_required
    @validate_params(Param('keyword', GET, str))
    def get_seller_name_list(keyword):

        """ 마스터 권한으로 상품 등록시 셀러를 검색하는 엔드포인트

        마스터 권한으로 접속하여 상품을 등록할 경우,
        셀러를 한글 이름으로 검색하여 선택할 수 있음

        Args:
            keyword: 셀러 한글 이름으로 검색할 키워드

        Returns:
            200: 검색된 셀러 10개 반환
            400: 데이터베이스 연결 에러
            500: server error

        Authors:

            leesh3@brandi.co.kr (이소헌)

        History:
            2020-04-04 (leesh3@brandi.co.kr): 초기 생성
        """

        db_connection = get_db_connection()
        if db_connection:
            try:
                seller_service = SellerService()
                seller_name_list_result = seller_service.get_seller_name_list(keyword, db_connection)

                return seller_name_list_result

            except Exception as e:
                return jsonify({'message': f'{e}'}), 400

    @seller_app.route('/login', methods=['POST'])
    @validate_params(
        Param('login_id', JSON, str),
        Param('password', JSON, str)
    )
    def login(*args):

        """ 셀러 로그인 엔드포인트
        셀러 로그인 엔드포인트 입니다.
        login_id와 password를 받습니다.

        request.body:
            login_id: 로그인 아이디
            password: 로그인 비밀번호

        Args:
            *args: 유효성 검사를 통과한 request.body의 인자

        Returns:
            200: SUCCESS 로그인 성공
            500: NO_DATABASE_CONNECTION

        Authors:
            choiyj@brandi.co.kr (최예지)

        History:
            2020-04-04 (choiyj@brandi.co.kr): 초기 생성
            2020-04-04 (choiyj@brandi.co.kr): account_info 에 필요한 정보 담음, DB 열림닫힘 여부에 따라 실행되는 함수 작성
        """

        # validation 확인이 된 data 를 account_info 로 재정의
        account_info = {
            'login_id': args[0],
            'password': args[1]
        }

        # DB에 연결
        db_connection = get_db_connection()

        # DB가 열렸을 경우
        if db_connection:
            try:
                # service 에 있는 SellerService 를 가져와서 seller_service 라는 인스턴스를 만듬
                seller_service = SellerService()

                # 로그인 함수를 실행한 결과값을 login_result 에 저장
                login_result = seller_service.login(account_info, db_connection)

                return login_result

            # 정의하지 않은 모든 error 를 잡아줌
            except Exception as e:
                return jsonify({'message': f'{e}'}), 400

            # try 랑 except 에 상관없이 무조건 실행
            finally:
                try:
                    db_connection.close()
                except Exception as e:
                    return jsonify({'message': f'{e}'}), 400
        # DB가 열리지 않았을 경우
        else:
            return jsonify({'message': 'NO_DATABASE_CONNECTION'}), 500

    @seller_app.route('/status', methods=['PUT'], endpoint='change_seller_status')
    @login_required
    def change_seller_status():
        """ 마스터 권한으로 셀러 상태 변경

        Returns:
            200: 셀러 상태 변경 성공

        Authors:
            yoonhc@barndi.co.kr (윤희철)

        History:
            2020-04-05 (yoonhc@brandi.co.kr): 초기 생성
        """
        db_connection = get_db_connection()

        # 유저정보를 가져와 서비스로 넘김
        user = g.account_info
        seller_service = SellerService()
        status_change_result = seller_service.change_seller_status(request, user, db_connection)
        return status_change_result

    @seller_app.route('', methods=['POST'])
    @validate_params(
        Param('login_id', JSON, str,
              rules=[Pattern(r'^[a-zA-Z0-9]{1}[a-zA-Z0-9_-]{4,19}')]),
        Param('password', JSON, str,
              rules=[MaxLength(80)]),
        Param('password', JSON, str,
              rules=[MinLength(4)]),
        Param('contact_number', JSON, str,
              rules=[Pattern(r'^[0-9]{3}-{1}[0-9]{4}-{1}[0-9]{4}$')]),
        Param('seller_type_id', JSON, int),
        Param('name_kr', JSON, str,
              rules=[Pattern(r'^[가-힣a-zA-Z0-9\ ]{1,45}$')]),
        Param('name_en', JSON, str,
              rules=[Pattern(r'^[a-z\ ]{1,45}$')]),
        Param('center_number', JSON, str,
              rules=[Pattern(r'^[0-9]{2,3}-{1}[0-9]{3,4}-{1}[0-9]{4}$')]),
        Param('site_url', JSON, str,
              rules=[Pattern(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")]),
        Param('site_url', JSON, str,
              rules=[MaxLength(200)]),
        Param('kakao_id', JSON, str, required=False,
              rules=[Pattern(r'^[가-힣a-zA-Z0-9]{1,45}$')]),
        Param('insta_id', JSON, str, required=False,
              rules=[Pattern(r'^[a-zA-Z0-9]{1,45}$')]),
        Param('seller_type_id', JSON, str,
              rules=[Pattern(r"^[1-7]{1}$")])
    )
    def sign_up(*args):

        """ 계정 회원가입 엔드포인트

        회원가입 엔드포인트 입니다.
        request.body 로 회원가입에 필요한 정보를 받고,
        유효성 검사를 마친 정보를 account_info 에 담아
        service 에 전달합니다.

        Args:
            *args: 유효성 검사를 통과한 파라미터

        request.body:
            login_id 로그인 아이디 str
            password 비밀번호 str
            contact_number 담당자 번호 str
            seller_type_id 셀러 속성 아이디 int
            name_kr 셀러명 str
            name_en 셀러 영문명 str
            center_number 고객센터 번호 str
            site_url 사이트 URL str
            kakao_id 카카오 아이디 str required=False
            insta_id 인스타 아이디 str required=False

        Returns: http 응답코드
            200: SUCCESS 셀러 회원가입 완료
            400: EXISTING_LOGIN_ID, EXISTING_NAME_KR,
                 EXISTING_NAME_EN, INVALID_KEY
            500: NO_DATABASE_CONNECTION

        Authors:
            leejm3@brandi.co.kr (이종민)

        History:
        2020-04-06 (leejm3@brandi.co.kr): 초기 생성
        2020-04-07 (leejm3@brandi.co.kr):
            'center_number'의 중간부분 유효성검사 허용 범위를 4글자->3~4글자로 변경

        """

        # validation 확인이 된 data 를 account_info 로 재정의
        account_info = {
            'login_id': args[0],
            'password': args[1],
            'contact_number': args[3],
            'seller_type_id': args[4],
            'name_kr': args[5],
            'name_en': args[6],
            'center_number': args[7],
            'site_url': args[8],
            'kakao_id': args[10],
            'insta_id': args[11]
        }

        # 데이터베이스 연결
        db_connection = get_db_connection()
        if db_connection:
            try:
                seller_service = SellerService()

                sign_up_result = seller_service.sign_up(account_info, db_connection)
                return sign_up_result

            except Exception as e:
                return jsonify({'message': f'{e}'}), 400

            finally:
                try:
                    db_connection.close()
                except Exception as e:
                    return jsonify({'message': f'{e}'}), 400
        else:
            return jsonify({'message': 'NO_DATABASE_CONNECTION'}), 500
